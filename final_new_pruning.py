# -*- coding: utf-8 -*-
"""final new_pruning.ipynb

Automatically generated by Colaboratory.


"""

pip install -q tensorflow-model-optimization

import tempfile
import zipfile
import os
import h5py
import numpy as np
import glob
import math
from numpy import linalg as LA
from scipy.stats import rankdata
from shutil import copyfile, move
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches

import numpy as np
import tensorflow as tf
from tensorflow_model_optimization.python.core.sparsity.keras import prune
from tensorflow_model_optimization.python.core.sparsity.keras import pruning_callbacks
from tensorflow_model_optimization.python.core.sparsity.keras import pruning_schedule
from tensorflow_model_optimization.python.core.sparsity.keras import pruning_wrapper

keras = tf.keras
K = tf.keras.backend

# Commented out IPython magic to ensure Python compatibility.
# %load_ext tensorboard
import tensorboard

# Commented out IPython magic to ensure Python compatibility.
logdir = tempfile.mkdtemp()
print('Writing training logs to ' + logdir)
# %tensorboard --logdir={logdir}

callbacks = [tf.keras.callbacks.TensorBoard(log_dir=logdir, profile_batch=0)]
max_features = 20000
maxlen = 100  # cut texts after this number of words
batch_size = 32

print("Loading data...")
(x_train, y_train), (x_test, y_test) = keras.datasets.imdb.load_data(num_words=max_features)
print(len(x_train), "train sequences")
print(len(x_test), "test sequences")

print("Pad sequences (samples x time)")
x_train = keras.preprocessing.sequence.pad_sequences(x_train, maxlen=maxlen)
x_test = keras.preprocessing.sequence.pad_sequences(x_test, maxlen=maxlen)
print("x_train shape:", x_train.shape)
print("x_test shape:", x_test.shape)

print("Build model...")
model = keras.models.Sequential()
model.add(keras.layers.Embedding(max_features, 128, input_length=maxlen))
model.add(keras.layers.LSTM(128))  
model.add(keras.layers.Dense(1))
model.add(keras.layers.Activation("sigmoid"))

model.compile(
    loss=tf.keras.losses.binary_crossentropy,
    optimizer='adam',
    metrics=['accuracy'])

model.fit(x_train, y_train,
          batch_size=batch_size,
          epochs=3,
          verbose=1,
          callbacks=callbacks,
          validation_data=(x_test, y_test))

score = model.evaluate(x_test, y_test)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

model.summary()

model.weights

for layer in model.layers:
    print(layer.input_shape)

for layer in model.layers:
    print(layer.output_shape)

#Save model
_, model_file = tempfile.mkstemp('.h5')
tf.keras.models.save_model(model, model_file, include_optimizer=False)

weight=model.load_weights(model_file)

lay=[]
def print_attrs(name, obj):
    # Create indent
    shift = name.count('/') * '    '
    item_name = name.split("/")[-1]
    print(shift + item_name)
    try:
        for key, val in obj.attrs.items():
            if(key=='weight_names'):
              lay.append(val[0])
              print(shift + '    ' + f"{key}: {val}")
    except:
        pass


for k in [0.4,0.7,.80,.84,.88, .92, .94, .98, .99]:
    copyfile(model_file,"/tmp/orig.h5")
    f = h5py.File("/tmp/orig.h5",'r+')
    f.visititems(print_attrs)
    m=0
    for i in list(f.get('model_weights'))[:-1]:
      if(i=="activation" ):
        continue
      elif(i=="dense"):
        m=m+1
        continue
      else:
        data=f['model_weights'][i][lay[m]]
        w=np.array(data)
        print(w.shape)
        x=np.sort(w)
        y=np.sort(x,axis=0)
        for i in range(math.ceil((y.shape[0])*k)):
          for j in range(math.ceil((y.shape[1])*k)):
            y[i][j]=0
        #print(y.shape[0]*0.4,y.shape[1]*0.4)
        print(y)
        data[...]=y
        m=m+1
      
    f.close()
    move("/tmp/orig.h5","/tmp/weight_"+str(k)+".h5")


#print(list(f.items()))
'''d=f.get('model_weights')
k=d.items()
print(list(k))
p=d.get('/model_weights/dense/dense/kernel:0')
print(np.array(p))
p[...]=0
f=d.get('/model_weights/dense/dense/kernel:0')
print(np.array(f))
m=0
ranks={}
prued=[]
for l in list(f['model_weights'])[:-1]:
      if(l=='activation_2'):
        continue
      else:
        print(f['model_weights'].items())
      data = f['model_weights'][l][l][kernels[m]]
        w = np.array(data)
        ranks[l]=(rankdata(np.abs(w),method='dense') - 1).astype(int).reshape(w.shape)
        lower_bound_rank = np.ceil(np.max(ranks[l])*.3).astype(int)
        ranks[l][ranks[l]<=lower_bound_rank] = 0
        ranks[l][ranks[l]>lower_bound_rank] = 1
        w = w*ranks[l]
        print(w)
        data[...] = w
        prued.append(data)
        #f['model_weights']=w
        m=m+1'''

lay1=[]
def print_attrs(name, obj):
    # Create indent
    shift = name.count('/') * '    '
    item_name = name.split("/")[-1]
    print(shift + item_name)
    try:
        for key, val in obj.attrs.items():
            if(key=='weight_names'):
              lay1.append(val[0])
              print(shift + '    ' + f"{key}: {val}")
    except:
        pass


for k in [0.2,0.3,0.4,0.5,0.7,.80,.84,.88, .92, .94, .98, .99]:
    copyfile(model_file,"/tmp/orig.h5")
    f = h5py.File("/tmp/orig.h5",'r+')
    f.visititems(print_attrs)
    m=0
    for i in list(f.get('model_weights'))[:-1]:
      if(i=="activation" ):
        continue
      elif(i=="dense"):
        m=m+1
        continue
      else:
        data=f['model_weights'][i][lay1[m]]
        w=np.array(data)
        ind = np.unravel_index(np.argsort(w, axis=None), w.shape)
        for i in range(int(len(ind[0])*k)):
          w[ind[0][i]][ind[1][i]]=0
        data[...]=w
        m=m+1
      
    f.close()
    move("/tmp/orig.h5","/tmp/weight_"+str(k)+".h5")

files_weights = glob.glob('/tmp/weight_*.h5')
files_weights.sort()
accuracy_weights = []

for f in files_weights:
  restored_model = tf.keras.models.load_model(f,compile=False)
  restored_model.compile(
    loss=tf.keras.losses.binary_crossentropy,
    optimizer='adam',
    metrics=['accuracy'])
  score = restored_model.evaluate(x_test, y_test, verbose=1)
  #fl = h5py.File(f)
  params=0
#   for l in list(fl['model_weights']):
#     val = np.array(fl['model_weights'][l][l]['kernel:0'])
#     params += val[val>0].shape[0]
  accuracy_weights.append(score[1])
#   print('Params ',params)
#   print('Model ',f)
#   print('Test accuracy:', score[1])

accuracy_weights

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
plt.rcParams['figure.constrained_layout.use'] = True
plt.xlabel('% sparsity')
plt.ylabel('% accuracy')
#red_patch = mpatches.Patch(color='red', label='Neuron Pruning')
blue_patch = mpatches.Patch(color='blue',label='Weight Pruning')
plt.legend(handles=[blue_patch],loc='upper right')
#plt.plot([.25, .50, .60, .70, .80, .90, .95, .97, .99],accuracy_neurons,color='red')
plt.plot([ 40,70,80,84,88, 92, 94, 98, 99],accuracy_weights,color='blue')
plt.show()

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
plt.rcParams['figure.constrained_layout.use'] = True
plt.xlabel('% sparsity')
plt.ylabel('% accuracy')
#red_patch = mpatches.Patch(color='red', label='Neuron Pruning')
blue_patch = mpatches.Patch(color='blue',label='Weight Pruning')
plt.legend(handles=[blue_patch],loc='upper right')
#plt.plot([.25, .50, .60, .70, .80, .90, .95, .97, .99],accuracy_neurons,color='red')
plt.plot([20,30,40,50,70,80,84,88,92,94,98,99],accuracy_weights,color='blue')
plt.show()

'''restored_model = tf.keras.models.load_model("/tmp/tmpqeybrk44.h5",compile=True)
restored_model.compile(
     loss=tf.keras.losses.binary_crossentropy,
     optimizer='adam',
     metrics=['accuracy'])'''
restored_model.fit(x_train, y_train,
           batch_size=batch_size,
           epochs=1,
           verbose=1,
           validation_data=(x_test, y_test))
score = restored_model.evaluate(x_test, y_test, verbose=0)
tf.keras.models.save_model(restored_model, '/tmp/pruned_retrained.h5', include_optimizer=False)
print('Test loss:', score[0])
print('Test accuracy:', score[1])

tf.keras.models.save_model(restored_model, '/tmp/pruned_retrained.h5', include_optimizer=False)

"""**Memory Analysis after weight pruning**"""

#for upruned model
memory=[]
_, zip1 = tempfile.mkstemp('.zip') 
with zipfile.ZipFile(zip1, 'w', compression=zipfile.ZIP_DEFLATED) as f:
  f.write(model_file)
print("Size of the unpruned model before compression: %.2f Mb" % 
      (os.path.getsize(model_file) / float(2**20)))
print("Size of the unpruned model after compression: %.2f Mb" % 
      (os.path.getsize(zip1) / float(2**20)))
memory=[]
memory.append((os.path.getsize(zip1) / float(2**20)))

pruned_keras_files = files_weights
for pruned_keras_file in pruned_keras_files:
  _, zip2 = tempfile.mkstemp('.zip') 
  with zipfile.ZipFile(zip2, 'w', compression=zipfile.ZIP_DEFLATED) as f:
    f.write(pruned_keras_file)
  memory.append((os.path.getsize(zip2) / float(2**20)))
  print("Size of the pruned model before compression: %.2f Mb" % 
    (os.path.getsize(pruned_keras_file) / float(2**20)))
  print("Size of the pruned model after compression: %.2f Mb" % 
    (os.path.getsize(zip2) / float(2**20)))

print(memory)

plt.rcParams['figure.constrained_layout.use'] = True
plt.xlabel('% sparsity')
plt.ylabel('memory size in MB')

blue_patch = mpatches.Patch(color='blue',label='Weight Pruning')
plt.legend(handles=[blue_patch],loc='upper right')
#plt.plot([.25, .50, .60, .70, .80, .90, .95, .97, .99],accuracy_neurons,color='red')
plt.plot([0,20,30,40,50,70,80,84,88, 92,94,98,99],memory,color='blue')
plt.show()

"""# **Neuron** **Pruning**"""

lay2=[]
def print_attrs(name, obj):
    # Create indent
    shift = name.count('/') * '    '
    item_name = name.split("/")[-1]
    print(shift + item_name)
    try:
        for key, val in obj.attrs.items():
            if(key=='weight_names'):
              lay2.append(val[0])
              print(shift + '    ' + f"{key}: {val}")
    except:
        pass


for k in [0.1,0.2,0.3,0.4,0.5,0.6,0.7,.80]:
    copyfile(model_file,"/tmp/orig.h5")
    f = h5py.File("/tmp/orig.h5",'r+')
    f.visititems(print_attrs)
    m=0
    for i in list(f.get('model_weights'))[:-1]:
      if(i=="activation" ):
        continue
      elif(i=="dense"):
        m=m+1
        continue
      else:
        data=f['model_weights'][i][lay2[m]]
        w=np.array(data)
  
        ind = np.argsort(LA.norm(w, axis=0))
        index_len=int(len(ind)*k)
        for i in range(index_len):
          w[:,ind[i]]=0
        data[...]=w
        m=m+1
      
    f.close()
    move("/tmp/orig.h5","/tmp/neuron_"+str(k)+".h5")

files_neurons = glob.glob('/tmp/neuron_*.h5')
files_neurons.sort()
accuracy_neurons = []

for f in files_neurons:
  restored_model_2 = tf.keras.models.load_model(f,compile=False)
  restored_model_2.compile(
    loss=tf.keras.losses.binary_crossentropy,
    optimizer='adam',
    metrics=['accuracy'])
  score = restored_model_2.evaluate(x_test, y_test, verbose=1)
  accuracy_neurons.append(score[1])

import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
plt.rcParams['figure.constrained_layout.use'] = True
plt.xlabel('% sparsity')
plt.ylabel('% accuracy')
red_patch = mpatches.Patch(color='red', label='Neuron Pruning')
plt.legend(handles=[red_patch],loc='upper right')
#plt.plot([.25, .50, .60, .70, .80, .90, .95, .97, .99],accuracy_neurons,color='red')
plt.plot([10,20,30,40,50,60,70,80],accuracy_neurons,color='red')
plt.show()

#for upruned model
memory1=[]
_, zip1 = tempfile.mkstemp('.zip') 
with zipfile.ZipFile(zip1, 'w', compression=zipfile.ZIP_DEFLATED) as f:
  f.write(model_file)
print("Size of the unpruned model before compression: %.2f Mb" % 
      (os.path.getsize(model_file) / float(2**20)))
print("Size of the unpruned model after compression: %.2f Mb" % 
      (os.path.getsize(zip1) / float(2**20)))

memory1.append((os.path.getsize(zip1) / float(2**20)))

pruned_files = files_neurons
for pruned_keras_file in pruned_files:
  _, zip2 = tempfile.mkstemp('.zip') 
  with zipfile.ZipFile(zip2, 'w', compression=zipfile.ZIP_DEFLATED) as f:
    f.write(pruned_keras_file)
  memory.append((os.path.getsize(zip2) / float(2**20)))
  print("Size of the pruned model before compression: %.2f Mb" % 
    (os.path.getsize(pruned_keras_file) / float(2**20)))
  print("Size of the pruned model after compression: %.2f Mb" % 
    (os.path.getsize(zip2) / float(2**20)))

plt.rcParams['figure.constrained_layout.use'] = True
plt.xlabel('% sparsity')
plt.ylabel('memory size in MB')

blue_patch = mpatches.Patch(color='blue',label='Weight Pruning')
plt.legend(handles=[blue_patch],loc='upper right')
plt.plot([0,10,20,30,40,50,60,70,80],memory,color='blue')
plt.show()