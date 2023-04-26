import pytest
import tensorflow as tf
import numpy as np

from transformerx.layers import TransformerEncoder


class TestTransformerEncoder:
    @pytest.fixture(scope="class")
    def encoder(self):
        return TransformerEncoder(
            vocab_size=1000, max_len=50, d_model=128, num_heads=4, n_blocks=2
        )

    def test_embedding_output_shape(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        embedded_data = encoder.embedding(input_data)
        assert embedded_data.shape == (2, 3, 128)

    def test_positional_encoding_output_shape(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        embedded_data = encoder.embedding(input_data)
        pos_encoded_data = encoder.pos_encoding(embedded_data)
        assert pos_encoded_data.shape == (2, 3, 128)

    def test_encoder_block_output_shape(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        valid_lens = tf.constant([3, 2], dtype=tf.float32)
        embedded_data = encoder.embedding(input_data)
        pos_encoded_data = encoder.pos_encoding(embedded_data)
        block_output, block_attn_weights = encoder.blocks[0](
            pos_encoded_data, pos_encoded_data, pos_encoded_data
        )
        assert block_output.shape == (2, 3, 128)

    def test_encoder_output_shape(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        valid_lens = tf.constant([3, 2], dtype=tf.float32)
        output, attn_weights = encoder(input_data, input_data, input_data)
        assert output.shape == (2, 3, 128)

    def test_encoder_output_values(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        valid_lens = tf.constant([3, 2], dtype=tf.float32)
        output, attn_weights = encoder(input_data, input_data, input_data)
        assert not np.allclose(output.numpy(), np.zeros((2, 3, 128)))

    def test_encoder_attention_weights_shape(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        valid_lens = tf.constant([3, 2], dtype=tf.float32)
        _ = encoder(input_data, input_data, input_data)
        for attention_weights in encoder.attention_weights:
            assert attention_weights.shape == (2, 4, 3, 3)

    def test_encoder_attention_weights_values(self, encoder):
        input_data = tf.constant([[1, 2, 3], [4, 5, 6]], dtype=tf.int32)
        valid_lens = tf.constant([3, 2], dtype=tf.float32)
        _ = encoder(input_data, input_data, input_data)
        for attention_weights in encoder.attention_weights:
            assert not np.allclose(attention_weights.numpy(), np.zeros((2, 4, 3, 3)))


class TestTransformerEncoderIntegration:
    @staticmethod
    def create_toy_dataset(num_samples=100, seq_length=10, vocab_size=50):
        X = np.random.randint(0, vocab_size, size=(num_samples, seq_length))
        y = np.random.randint(0, 2, size=(num_samples, 1))
        return X, y

    @pytest.fixture(scope="class")
    def model(self):
        seq_length = 10
        vocab_size = 50
        inputs = tf.keras.layers.Input(shape=(seq_length,))
        valid_lens = tf.keras.layers.Input(shape=())
        encoder = TransformerEncoder(vocab_size=vocab_size, max_len=seq_length)
        outputs, attn_weights = encoder(inputs, inputs, inputs)
        pooled_output = tf.keras.layers.GlobalAveragePooling1D()(outputs)
        predictions = tf.keras.layers.Dense(1, activation="sigmoid")(pooled_output)
        model = tf.keras.Model(inputs=[inputs], outputs=predictions)
        model.compile(
            optimizer="adam", loss="binary_crossentropy", metrics=["accuracy"]
        )
        return model

    def test_training(self, model):
        X, y = self.create_toy_dataset()
        history = model.fit(X, y, epochs=5, batch_size=32, validation_split=0.2)
        assert (
            history.history["accuracy"][-1] > 0.5
        ), "Training accuracy should be greater than 0.5"

    def test_evaluation(self, model):
        X, y = self.create_toy_dataset()
        history = model.fit(X, y, epochs=5, batch_size=32, validation_split=0.2)
        loss, accuracy = model.evaluate(X, y)
        assert accuracy > 0.5, "Evaluation accuracy should be greater than 0.5"

    def test_prediction(self, model):
        X, _ = self.create_toy_dataset(num_samples=1)
        prediction = model.predict(X)
        assert (
            0 <= prediction <= 1
        ), "Prediction should be a probability value between 0 and 1"