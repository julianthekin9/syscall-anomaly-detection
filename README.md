# syscall-anomaly-detection

## Встановлення

```
pip install -e .            # пакет syscall_hids і команди hids-train / hids-eval / hids-detect
```

`hids-detect` використовує eBPF через BCC. BCC не ставиться через pip, лише системним пакетом:

```
sudo apt install python3-bpfcc
```
