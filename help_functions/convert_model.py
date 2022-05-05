import tensorflow as tf
from  tensorflow import keras


# Convert the model.
model = keras.models.load_model('./Digital-Readout_Version_6.0.0.h5')
converter = tf.lite.TFLiteConverter.from_keras_model(model)
tflite_model = converter.convert()

# Save the model.
with open('./model_digital_number.tflite', 'wb') as f:
  f.write(tflite_model)
