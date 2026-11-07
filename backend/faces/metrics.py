"""Report actual held-out predictions; never translate embedding movement into protection."""
import numpy as np


def summarize(labels, clean_predictions, cloaked_predictions, target):
    labels, clean, cloaked = map(np.asarray, (labels, clean_predictions, cloaked_predictions))
    if len(labels) == 0 or labels.shape != clean.shape or labels.shape != cloaked.shape:
        raise ValueError('Prediction arrays must have equal, nonzero lengths.')
    selected = labels == target
    if not selected.any():
        raise ValueError('Target identity has no held-out photos.')
    baseline = int(np.sum(clean[selected] == labels[selected]))
    protected = int(np.sum(cloaked[selected] == labels[selected]))
    count = int(selected.sum())
    return {'target':target, 'test_count':count, 'baseline_correct':baseline,
        'cloaked_correct':protected, 'baseline_accuracy':baseline/count,
        'cloaked_accuracy':protected/count, 'drop_percentage_points':100*(baseline-protected)/count,
        'interpretation': 'inconclusive-low-baseline' if baseline/count < 0.8 else
            'reduced-recognition-in-this-test' if protected < baseline else 'no-reduction-in-this-test',
        'scope':'Frozen FaceNet encoder + fitted logistic classifier; not full network fine-tuning or universal protection.',
        'predictions':[{'truth':str(y),'baseline':str(a),'cloaked':str(b)} for y,a,b in zip(labels,clean,cloaked)]}
