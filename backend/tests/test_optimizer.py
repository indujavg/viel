import threading
import unittest
import torch
from backend.optimizer import optimize, Cancelled

class OptimizerTest(unittest.TestCase):
    def test_real_gradients_reduce_objective_inside_budget(self):
        image=torch.full((1,3,8,8),0.8)
        result,metrics=optimize(image,lambda x:x*2,epsilon=8/255,steps=20,seed=42)
        self.assertLess(metrics['objective_after'],metrics['objective_before'])
        self.assertLessEqual(float((result-image).abs().max()),8/255+1e-7)
        self.assertTrue(torch.equal(image,torch.full_like(image,0.8)))
        repeat,_=optimize(image,lambda x:x*2,epsilon=8/255,steps=20,seed=42)
        self.assertTrue(torch.equal(result,repeat))

    def test_cancellation(self):
        cancel=threading.Event();cancel.set()
        with self.assertRaises(Cancelled):
            optimize(torch.zeros(1,3,8,8),lambda x:x,epsilon=4/255,steps=10,seed=42,cancel=cancel)

    def test_invalid_budget(self):
        with self.assertRaises(ValueError):
            optimize(torch.zeros(1,3,8,8),lambda x:x,epsilon=1,steps=10,seed=42)

if __name__=='__main__':unittest.main()
