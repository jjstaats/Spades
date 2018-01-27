import tensorflow as tf
import game_state

class Trainer:
	def __main__():
		t = Trainer("/tmp/model")
		t.queue_sample(GameState())
		t.set_label(10)
		t.train()

	def __init__(self, model_dir):
		self.estimator = tf.estimator.Estimator(
			model_fn = model.create_model,
			config = tf.learn.RunConfig(
				model_dir = Model.create_trainer,
			),
			params = {
				'size': 12,
				'regularizer': 0.001,
				'numbers_weight': 0.01,
				'learnrate': 0.003,
			},
		)

		self.samples = []
		self.queue = []

	def queue_sample(self, sample):
		self.queue.append(sample.to_features())

	def set_label(self, label):
		for sample in self.queue:
			self.samples.append((sample, label))
		self.queue = []
	
	def train(self):
		data = (tf.data.Dataset.range(len(self.samples))
			.map(lambda i: self.samples[i])
			.repeat()
			.shuffle(1024)
			.batch(32))

		iterator = data.make_one_shot_iterator().get_next()

		self.estimator.train(
			input_fn = iterator,
			steps = 1000,
		)