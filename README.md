# syscall-anomaly-detection

## Встановлення

```
pip install -e .            # пакет syscall_hids і команди hids-train / hids-eval / hids-detect
pip install -e .[testbed]   # + залежності тестового стенду flask_app
```

`hids-detect` і збір трас у `flask_app/` використовують eBPF через BCC. BCC не ставиться через pip, лише системним пакетом:

```
sudo apt install python3-bpfcc
```
