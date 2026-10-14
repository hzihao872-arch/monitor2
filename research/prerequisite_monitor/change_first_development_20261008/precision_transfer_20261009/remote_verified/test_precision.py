import types,unittest,torch
from head_precision import enable_fp32_head
class Test(unittest.TestCase):
 def test_head_cast_only(self):
  m=types.SimpleNamespace(config=types.SimpleNamespace(tie_word_embeddings=False),lm_head=torch.nn.Linear(3,4,bias=False).to(torch.bfloat16),body=torch.nn.Linear(3,3).to(torch.bfloat16));w=m.lm_head.weight.detach().float().clone();x=torch.tensor([[1.,2.,3.]],dtype=torch.bfloat16);h=enable_fp32_head(m);out=m.lm_head(x);self.assertEqual(out.dtype,torch.float32);self.assertEqual(m.body.weight.dtype,torch.bfloat16);self.assertTrue(torch.equal(m.lm_head.weight,w));self.assertTrue(torch.equal(out,torch.nn.functional.linear(x.float(),w)));h.remove()
 def test_tied_rejected(self):
  m=types.SimpleNamespace(config=types.SimpleNamespace(tie_word_embeddings=True),lm_head=torch.nn.Linear(3,4).to(torch.bfloat16))
  with self.assertRaises(ValueError):enable_fp32_head(m)
  self.assertEqual(m.lm_head.weight.dtype,torch.bfloat16)
if __name__=='__main__':unittest.main()
