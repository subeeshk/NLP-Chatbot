import torch
import random

from seq2seq import Encoder, Decoder, AttnDecoderRNN

# Inspired by http://pytorch.org/tutorials/intermediate/seq2seq_translation_tutorial.html
# and https://github.com/tensorflow/nmt

class Seq2Seq:
	def __init__(self,
				 #encoder, decoder, encoder_optimizer, decoder_optimizer, criterion,
				 input_vocabulary_dim, target_vocabulary_dim, #target_max_length,
				 go_symbol_idx, eos_symbol_idx,
				 embedding_dim,
				 embedding_matrix_encoder=None, embedding_matrix_decoder=None,
				 embedding_padding_idx=None):
		# hparams:
		bidirectional = False
		n_layers = 1
		
		#encoder_input_size = input_vocabulary_dim
		encoder_hidden_size = 300
		decoder_hidden_size = 300
		#decoder_output_size = target_vocabulary_dim
		
		#self.target_max_length = target_max_length
		
		self.GO_SYMBOL_IDX = go_symbol_idx
		self.EOS_SYMBOL_IDX = eos_symbol_idx
	
		# Encoder:
		self.encoder = Encoder.Encoder(input_vocabulary_dim,
									   embedding_dim,
									   encoder_hidden_size,
									   n_layers,
									   bidirectional,
									   embedding_matrix_encoder,
									   embedding_padding_idx)
									   
		# Decoder:
		self.decoder = Decoder.Decoder(target_vocabulary_dim,
									   embedding_dim,
									   decoder_hidden_size,
									   n_layers,
									   bidirectional,
									   embedding_matrix_decoder,
									   embedding_padding_idx)
		#self.decoder = AttnDecoderRNN.AttnDecoderRNN(decoder_hidden_size,
		#											 decoder_output_size,
		#											 self.target_max_length,
		#											 decoder_n_layers,
		#											 0.1,
		#											 embedding_matrix_decoder)
									   
		if torch.cuda.is_available():
			self.encoder = self.encoder.cuda()
			self.decoder = self.decoder.cuda()
											   
		# Optimizers:
		self.encoder_optimizer = torch.optim.RMSprop(self.encoder.parameters())
		self.decoder_optimizer = torch.optim.RMSprop(self.decoder.parameters())
		
		# Loss (embedding_padding_idx is ignored, it does not contribute to input gradients):
		self.criterion = torch.nn.NLLLoss(ignore_index=embedding_padding_idx)

	def train(self, X, Y, batch_size): # TODO: add X_dev=None, Y_dev=None
		
		for idx in range(0, len(X), batch_size):
			x = torch.autograd.Variable(torch.LongTensor(X[idx:min(idx+batch_size, len(X))]))
			y = torch.autograd.Variable(torch.LongTensor(Y[idx:min(idx+batch_size, len(Y))]))
			
			if torch.cuda.is_available():
				x = x.cuda()
				y = y.cuda()
			
			self.encoder_optimizer.zero_grad()
			self.decoder_optimizer.zero_grad()

			input_length = x.size()[1]
			target_length = y.size()[1]

			#encoder_outputs = torch.autograd.Variable(torch.zeros(self.target_max_length, self.encoder.hidden_size))
			#encoder_outputs = encoder_outputs.cuda() if torch.cuda.is_available() else encoder_outputs

			loss = 0

			encoder_output, encoder_hidden = self.encoder(x)

			decoder_input = torch.autograd.Variable(torch.LongTensor([[self.GO_SYMBOL_IDX] * x.size()[0]]))
			decoder_input = decoder_input.cuda() if torch.cuda.is_available() else decoder_input
			
			decoder_hidden = encoder_hidden

			for di in range(target_length):
				decoder_output, decoder_hidden = self.decoder(decoder_input, decoder_hidden)
				topv, topi = decoder_output.data.topk(1)
			
				decoder_input = torch.autograd.Variable(torch.LongTensor(topi))
				decoder_input = decoder_input.cuda() if torch.cuda.is_available() else decoder_input
			
				loss += self.criterion(decoder_output, y[:,di])

			tot_loss = loss.data[0] / x.size()[0]
			print("Avg. loss at iteration " + str(int(idx/batch_size+1)) + ": " + str(tot_loss))

			loss.backward()

			self.encoder_optimizer.step()
			self.decoder_optimizer.step()
