# Запуск расчётов на Colab (инструкция для Claude Code)

Проект лежит на Windows. Официальный Colab CLI (`colab`) и SSH-хост `colab-ids` настроены в WSL, поэтому все команды к Colab идут через `wsl bash -lc`. `wsl` наследует текущую папку, так что относительные пути (`./outputs/...`) указывают в проект.

Справка по CLI — скилл `.claude/skills/colab-operator/SKILL.md`, читай его перед первой командой `colab` в сессии. Команды в нём написаны для Linux: при вызове из Windows оборачивай их в `wsl bash -lc "..."`.

## Как вызывать
- Команды `colab`:
  ```bash
  wsl bash -lc "colab status -s ids"
  ```
- Shell-команды на VM — только через heredoc, без вложенных кавычек:
  ```bash
  wsl bash -lc "ssh colab-ids bash -s" <<'EOF'
  cd /content/repo && git log --oneline -1
  EOF
  ```
- Если `ssh colab-ids` отвечает 404 или не подключается, используй `wsl bash -lc "colab console -s ids" <<'EOF' ... EOF` и фильтруй вывод через `grep -a`. Если и это не работает, остановись и скажи мне.

## Сессия
- Имя сессии всегда `ids`.
- VM создаю и останавливаю Я (`colab new`, `colab drivemount`, `colab stop`): `drivemount` интерактивный, а VM тратит compute units. Если `colab status -s ids` говорит, что сессии нет, скажи мне. Не создавай VM сам.

## Где что лежит на VM
- код: `/content/repo` (git-клон, `pip install -e .`);
- данные: `/content/data` (локальный диск VM, временный);
- результаты: `/content/drive/MyDrive/ids/runs` (Google Drive, переживают перезапуск VM).

## Правила
1. **Подготовка VM**, если её ещё не было в этой сессии. Клон приватного репозитория делаю я. Если `/content/repo` нет, скажи мне.
   ```bash
   wsl bash -lc "ssh colab-ids bash -s" <<'EOF'
   cd /content/repo && git fetch -q && git checkout -q main && git pull -q && pip install -q -e . && git rev-parse HEAD
   test -d /content/data/PHP_CWE-434 || (mkdir -p /content/data && tar -xzf /content/drive/MyDrive/ids/datasets/PHP_CWE-434.tar.gz -C /content/data)
   python -c "import torch; print('cuda', torch.cuda.is_available())"
   EOF
   ```
2. **Никаких долгих команд в foreground.** У Bash есть таймаут, а обрыв SSH убьёт процесс. Обучение запускается только в tmux:
   ```bash
   wsl bash -lc "ssh colab-ids bash -s" <<'EOF'
   tmux new -d -s train "cd /content/repo && hids-train --config configs/php_cwe_434.yaml --dataset_root /content/data --work_dir /content/drive/MyDrive/ids/runs 2>&1 | tee -a /content/drive/MyDrive/ids/runs/tmux_train.log"
   tmux ls
   EOF
   ```
3. **Код на VM только из git.** Сначала коммит и `git push` на Windows, потом `git pull` на VM. Файлы через `colab upload` не правь. В отчёт о запуске записывай `git rev-parse HEAD` с VM.
4. **Проверка прогресса** — короткими командами, не чаще раза в несколько минут:
   ```bash
   wsl bash -lc "ssh colab-ids bash -s" <<'EOF'
   tmux ls; tail -n 30 /content/drive/MyDrive/ids/runs/tmux_train.log
   nvidia-smi --query-gpu=utilization.gpu,memory.used --format=csv
   EOF
   ```
5. **Результаты** забирай в проект:
   ```bash
   wsl bash -lc "colab download -s ids /content/drive/MyDrive/ids/runs/<файл> ./outputs/<файл>"
   ```
6. **Когда обучение закончилось**, скажи мне, чтобы я остановил VM. Сам `colab stop` не вызывай.
7. **Нельзя:**
   - удалять что-либо в `/content/drive`;
   - запускать два обучения на одной GPU;
   - ставить пакеты, меняющие torch;
   - запускать eBPF (на Colab его нет);
   - вставлять токены и пароли в команды.