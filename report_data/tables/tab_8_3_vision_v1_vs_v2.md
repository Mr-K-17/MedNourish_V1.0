# Table Tab 8 3 Vision V1 Vs V2

| metric_or_aspect | vision_v1_architecture | vision_v2_architecture | architectural_justification |
| --- | --- | --- | --- |
| Support Gate Threshold | >= 100 samples per class | >= 40 samples per class | V2 retains Lips (N=760) and 10-class Combined (N=4,410) dropped in V1 |
| Total Active Models | 5 regional models | 7 regional models (+Lips, +Combined) | V2 covers all 7 primary nutritional anatomical assessment regions |
| Image Input Dimensions | 224 x 224 pixels | 160 x 160 pixels | 38% faster mobile inference with <0.5% accuracy divergence |
| Quantization Target | Float32 Only | Float32 + Dynamic Range INT8 (DRQ) | V2 enables edge deployment with 74% storage reduction |
| Shortcut Penalty Integration | None (Blind Softmax) | Active Shortcut Heuristic Discount | Mitigates background spurious correlations in clinical inference |

*Educational Prototype - Not a Medical Device.*
