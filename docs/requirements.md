# Current scope: Fawkes-style training privacy

The user changed the active goal to Fawkes-style face cloaking and a measured demonstration of its effect. Meta AI editing resistance was not achieved by the prior encoder experiment and is not claimed by this flow.

Required: website-only image selection, real upstream Fawkes integration, explicit processing consent, a separate held-out recognition experiment, actual predictions/metrics and failure outcomes, downloadable evidence, and no fabricated protection scores.

The implemented evaluation fits two identity classifiers on a frozen independent FaceNet encoder. It is a limited transfer-learning test, not full backbone training or a full reproduction of the Fawkes paper. Real protection requires measured recognition results and a separate assessment of visual similarity. See face-proof.md for setup, input layout, evidence limits, and data handling.
