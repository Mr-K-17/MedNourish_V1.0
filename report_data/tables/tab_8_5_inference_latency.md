# Table Tab 8 5 Inference Latency

| pipeline_stage | hardware_target | median_latency_ms | p95_latency_ms | max_latency_ms | throughput_fps |
| --- | --- | --- | --- | --- | --- |
| Image Quality Gate (Laplacian + Lum) | Intel Core i5 (Single Core) | 4.8 ms | 8.2 ms | 14.1 ms | 208.3 |
| MobileNetV2 Vision Inference (F32) | Intel Core i5 (AVX2) | 28.4 ms | 38.6 ms | 52.0 ms | 35.2 |
| MobileNetV2 Vision Inference (DRQ INT8) | Intel Core i5 (AVX2) | 14.2 ms | 19.5 ms | 26.3 ms | 70.4 |
| Tabular XGBoost Inference (24 feats) | Intel Core i5 (Single Core) | 1.2 ms | 2.1 ms | 3.8 ms | 833.3 |
| End-to-End MedScan Pipeline | Client-Server Localhost Loop | 42.6 ms | 58.4 ms | 78.2 ms | 23.5 |

*Educational Prototype - Not a Medical Device.*
