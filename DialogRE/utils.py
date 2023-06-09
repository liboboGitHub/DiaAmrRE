import numpy as np
import copy
import math
import torch
import torch.nn as nn
from torch.nn import ModuleList
import torch.nn.functional as F


def has_nan(tensor):
    return torch.isnan(tensor).any().item()


def _get_activation_fn(activation):
    if activation == "relu":
        return F.relu
    elif activation == "gelu":
        return F.gelu

    raise RuntimeError("activation should be relu/gelu, not {}".format(activation))


def _get_clones(module, N):
    return ModuleList([copy.deepcopy(module) for i in range(N)])


def universal_sentence_embedding(sentences, mask, length, sqrt=True):
    """
    sentences: [batch,seq,dim]
    mask: [batch,seq]
    length: [batch]
    return: [batch,dim]
    """
    sentence_sum = torch.bmm(sentences.permute(0, 2, 1), mask.unsqueeze(2).float()).squeeze(-1)  # [batch, dim]
    divisor = length.float().unsqueeze(dim=1)  # [batch, 1]
    assert (divisor == 0.0).any() is False
    if sqrt:
        divisor = divisor.sqrt()
    sentence_sum /= divisor
    return sentence_sum


def clip_and_normalize(word_probs, epsilon):
    word_probs = torch.clamp(word_probs, epsilon, 1.0 - epsilon)
    return word_probs / word_probs.sum(dim=-1, keepdim=True)


class PositionalEncoding(nn.Module):


    def __init__(self, d_model, dropout=0.1, max_len=5000):
        super(PositionalEncoding, self).__init__()
        self.dropout = nn.Dropout(p=dropout)

        pe = torch.zeros(max_len, d_model)
        position = torch.arange(0, max_len, dtype=torch.float).unsqueeze(1)
        div_term = torch.exp(torch.arange(0, d_model, 2).float() * (-math.log(10000.0) / d_model))
        pe[:, 0::2] = torch.sin(position * div_term)
        pe[:, 1::2] = torch.cos(position * div_term)
        pe = pe.unsqueeze(0).transpose(0, 1)
        self.register_buffer("pe", pe)

    def forward(self, x):

        x = x + self.pe[: x.size(0), :]  # [seq, 1, dim]
        return self.dropout(x)
