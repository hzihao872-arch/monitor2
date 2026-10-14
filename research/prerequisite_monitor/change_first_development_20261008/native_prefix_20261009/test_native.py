import unittest
from native_runner import causal_ids,video_times
class Test(unittest.TestCase):
 def test_no_future(self):
  self.assertEqual(causal_ids([{'evidence_id':f'f{i:04d}','time_ms':i*1000} for i in range(20)],14000),[f'f{i:04d}' for i in range(15)])
 def test_pair_time(self):
  self.assertEqual(video_times(15),[.5,2.5,4.5,6.5,8.5,10.5,12.5,14.0])
  self.assertEqual(video_times(1),[0.0])
if __name__=='__main__':unittest.main()
