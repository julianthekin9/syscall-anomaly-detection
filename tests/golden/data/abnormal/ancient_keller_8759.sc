1631268063036264810 apache2 getsockname >
1631268063036265743 apache2 getsockname <
1631268063036273276 apache2 fcntl > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) cmd=4(F_GETFL) 
1631268063036273572 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063036273703 apache2 fcntl > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) cmd=5(F_SETFL) 
1631268063036273858 apache2 fcntl < res=0(<f>/dev/null) 
1631268063036297742 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063036300941 apache2 mmap < res=7F603424C000 vm_size=374020 vm_rss=9100 vm_swap=0 
1631268063036313422 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063036314177 apache2 mmap < res=7F603424A000 vm_size=374028 vm_rss=9100 vm_swap=0 
1631268063036315880 apache2 read > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=8000 
1631268063036319038 apache2 read < res=434 data=R0VUIC9sb2dpbi5waHAgSFRUUC8xLjENCkhvc3Q6IDM2NjgzYzVmYzMxY2VhMmINCkNvbm5lY3Rpb246IGtlZXAtYWxpdmUNClVwZ3JhZGU= 
1631268063036363538 apache2 stat >
1631268063036371593 apache2 stat < res=0 path=/var/www/html/login.php 
1631268063036386994 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063036388155 apache2 mmap < res=7F6034248000 vm_size=374036 vm_rss=9100 vm_swap=0 
1631268063036477102 apache2 brk > addr=55C5E443A000 
1631268063036479117 apache2 brk < res=55C5E443A000 vm_size=374224 vm_rss=9100 vm_swap=0 
1631268063036656129 apache2 brk > addr=55C5E445B000 
1631268063036657056 apache2 brk < res=55C5E445B000 vm_size=374356 vm_rss=11008 vm_swap=0 
1631268063036703465 apache2 setitimer >
1631268063036704908 apache2 setitimer <
1631268063036705291 apache2 rt_sigaction >
1631268063036705672 apache2 rt_sigaction <
1631268063036706235 apache2 rt_sigprocmask >
1631268063036706447 apache2 rt_sigprocmask <
1631268063036757097 apache2 mmap > addr=0 length=65536 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063036758118 apache2 mmap < res=7F6034238000 vm_size=374420 vm_rss=11312 vm_swap=0 
1631268063036783430 apache2 getcwd >
1631268063036784089 apache2 getcwd < res=2 path=/ 
1631268063036784798 apache2 chdir >
1631268063036786660 apache2 chdir < res=0 path=/var/www/html 
1631268063036788320 apache2 setitimer >
1631268063036788572 apache2 setitimer <
1631268063036793009 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.I1y8sF (deleted)) cmd=8(F_SETLK) 
1631268063036795790 apache2 fcntl < res=0(<f>/dev/null) 
1631268063036844216 apache2 getcwd >
1631268063036844732 apache2 getcwd < res=14 path=/var/www/html 
1631268063036899074 apache2 getpid >
1631268063036899592 apache2 getpid <
1631268063036907937 apache2 open >
1631268063036914742 apache2 open < fd=11(<f>/dev/urandom) name=/dev/urandom flags=1(O_RDONLY) mode=0 dev=1000FE 
1631268063036917944 apache2 read > fd=11(<f>/dev/urandom) size=32 
1631268063036918944 apache2 read < res=32 data=f3EwJnzn6ige2nopWa2TAaic4cfca/Id/bh6ezcyv7Y= 
1631268063036919673 apache2 close > fd=11(<f>/dev/urandom) 
1631268063036919985 apache2 close < res=0 
1631268063036923966 apache2 stat >
1631268063036937852 apache2 stat < res=-2(ENOENT) path=/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5 
1631268063036947368 apache2 open >
1631268063036967945 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) name=/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5 flags=7(O_CREAT|O_RDWR) mode=0600 dev=1000FA 
1631268063036968941 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) 
1631268063036969818 apache2 fstat < res=0 
1631268063036970077 apache2 getuid >
1631268063036970215 apache2 getuid < uid=33(www-data) 
1631268063036970517 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) operation=2(LOCK_EX) 
1631268063036972273 apache2 flock < res=0 
1631268063036972498 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) cmd=3(F_SETFD) 
1631268063036972765 apache2 fcntl < res=0(<f>/dev/null) 
1631268063036972937 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) 
1631268063036973422 apache2 fstat < res=0 
1631268063036982284 apache2 access > mode=0(F_OK) 
1631268063036985624 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268063037031348 apache2 getcwd >
1631268063037031889 apache2 getcwd < res=14 path=/var/www/html 
1631268063037035970 apache2 lstat >
1631268063037039825 apache2 lstat < res=0 path=/var/www/html/hackable/uploads 
1631268063037040346 apache2 lstat >
1631268063037041711 apache2 lstat < res=0 path=/var/www/html/hackable 
1631268063037042076 apache2 lstat >
1631268063037043301 apache2 lstat < res=0 path=/var/www/html 
1631268063037043598 apache2 lstat >
1631268063037044812 apache2 lstat < res=0 path=/var/www 
1631268063037045336 apache2 lstat >
1631268063037046415 apache2 lstat < res=0 path=/var 
1631268063037052378 apache2 getcwd >
1631268063037052717 apache2 getcwd < res=14 path=/var/www/html 
1631268063037053634 apache2 lstat >
1631268063037057815 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268063037058433 apache2 lstat >
1631268063037060068 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp 
1631268063037060577 apache2 lstat >
1631268063037062055 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS 
1631268063037062579 apache2 lstat >
1631268063037063993 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib 
1631268063037064429 apache2 lstat >
1631268063037065748 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6 
1631268063037066201 apache2 lstat >
1631268063037067712 apache2 lstat < res=0 path=/var/www/html/external/phpids 
1631268063037070286 apache2 lstat >
1631268063037071539 apache2 lstat < res=0 path=/var/www/html/external 
1631268063037073111 apache2 getcwd >
1631268063037073355 apache2 getcwd < res=14 path=/var/www/html 
1631268063037073827 apache2 lstat >
1631268063037075354 apache2 lstat < res=0 path=/var/www/html/config 
1631268063037086503 apache2 open >
1631268063037090989 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000FA 
1631268063037092308 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631268063037092692 apache2 lseek < res=0 
1631268063037093519 apache2 fstat > fd=12(<f>/etc/passwd) 
1631268063037094076 apache2 fstat < res=0 
1631268063037094238 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631268063037096287 apache2 mmap < res=7F603439B000 vm_size=374424 vm_rss=12892 vm_swap=0 
1631268063037096471 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631268063037096902 apache2 lseek < res=1022 
1631268063037101214 apache2 munmap > addr=7F603439B000 length=1022 
1631268063037103311 apache2 munmap < res=0 vm_size=374420 vm_rss=13772 vm_swap=0 
1631268063037103513 apache2 close > fd=12(<f>/etc/passwd) 
1631268063037103735 apache2 close < res=0 
1631268063037106882 apache2 access > mode=2(W_OK) 
1631268063037109280 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631268063037110380 apache2 access > mode=2(W_OK) 
1631268063037111607 apache2 access < res=0 name=/var/www/html/config 
1631268063037112247 apache2 access > mode=2(W_OK) 
1631268063037113974 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268063037149336 apache2 socket > domain=10(AF_INET6) type=2 proto=0 
1631268063037153624 apache2 socket < fd=12(<6>) 
1631268063037155524 apache2 close > fd=12(<6>) 
1631268063037155709 apache2 close < res=0 
1631268063037160620 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268063037163328 apache2 socket < fd=12(<4>) 
1631268063037163639 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631268063037163915 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063037164038 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631268063037164176 apache2 fcntl < res=0(<f>/dev/null) 
1631268063037164315 apache2 connect > fd=12(<4>) 
1631268063037196164 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:60502->127.0.0.1:3306 
1631268063037197495 apache2 poll > fds=12:435 timeout=60000 
1631268063037198448 apache2 poll < res=1 fds=12:44 
1631268063037198764 apache2 getsockopt >
1631268063037199234 mysqld poll < res=1 fds=20:41 
1631268063037199363 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268063037199814 apache2 fcntl > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037199993 apache2 fcntl < res=0(<f>/dev/null) 
1631268063037201487 apache2 setsockopt >
1631268063037201608 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268063037201885 mysqld fcntl < res=2(<p>pipe:[368810612]) 
1631268063037201983 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063037202084 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037202257 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037202382 apache2 setsockopt >
1631268063037202898 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063037202928 mysqld accept >
1631268063037204315 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037208367 mysqld accept < fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) tuple=127.0.0.1:60502->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268063037209105 mysqld fcntl > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268063037209241 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037209362 mysqld fcntl > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063037209497 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037209991 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037210106 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037210219 mysqld fcntl > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063037210317 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037232863 mysqld fcntl > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037233053 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037250970 mysqld setsockopt >
1631268063037252012 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268063037252356 mysqld setsockopt >
1631268063037252593 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063037253603 mysqld futex > addr=55C85FAC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268063037256442 mysqld futex < res=1 
1631268063037257063 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268063037262557 mysqld futex < res=0 
1631268063037264431 mysqld futex > addr=55C85FABEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268063037264926 mysqld futex < res=0 
1631268063037265811 mysqld gettid >
1631268063037266330 mysqld gettid <
1631268063037269702 mysqld getpeername >
1631268063037271712 mysqld getpeername <
1631268063037279300 mysqld setsockopt >
1631268063037280544 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063037284989 mysqld sendto > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=102 tuple=NULL 
1631268063037306626 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAqwAAAC9oQERyNlUoAP/3LQIAP6AVAAAAAAAAAAAAAGZKImZfKk8zUHYlTwA= 
1631268063037308099 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037309029 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037310158 mysqld poll > fds=41:43 timeout=10000 
1631268063037352719 apache2 poll < res=1 fds=12:41 
1631268063037353964 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037355329 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268063037361296 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037362041 apache2 poll < res=1 fds=12:41 
1631268063037362214 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=102 
1631268063037363356 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQCrAAAAL2hARHI2VSgA//ctAgA/oBUAAAAAAAAAAAAAZkoiZl8qTzNQdiVPAG15c3E= tuple=NULL 
1631268063037369679 apache2 sendto > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=106 tuple=NULL 
1631268063037385777 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABQWzv2hVycM6/Pib4mETVw9P3vjoABteXNxbF9uYXRpdmVfcGFzc3c= 
1631268063037387101 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037388126 mysqld poll < res=1 fds=41:41 
1631268063037389516 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037391103 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631268063037391813 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=102 
1631268063037393146 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFBbO/aFXJwzr8+JviYRNXD0/e+OgAG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631268063037399954 mysqld sendto > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=48 tuple=NULL 
1631268063037431424 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQAL2hARHI2VShmSiJmXypPM1B2JU8A 
1631268063037432325 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037433055 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037433654 mysqld poll > fds=41:43 timeout=10000 
1631268063037463647 apache2 poll < res=1 fds=12:41 
1631268063037464850 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037466262 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631268063037467965 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037468646 apache2 poll < res=1 fds=12:41 
1631268063037468832 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=102 
1631268063037469741 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZAAvaEBEcjZVKGZKImZfKk8zUHYlTwA= tuple=NULL 
1631268063037477670 apache2 sendto > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=24 tuple=NULL 
1631268063037491770 apache2 sendto < res=24 data=FAAAAxbO/aFXJwzr8+JviYRNXD0/e+Og 
1631268063037492842 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037493836 mysqld poll < res=1 fds=41:41 
1631268063037495170 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037496406 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631268063037496943 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=20 
1631268063037497920 mysqld recvfrom < res=20 data=Fs79oVcnDOvz4m+JhE1cPT9746A= tuple=NULL 
1631268063037503693 mysqld sendto > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=11 tuple=NULL 
1631268063037516945 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631268063037521296 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037538530 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037539051 mysqld poll > fds=41:43 timeout=28800000 
1631268063037573072 apache2 poll < res=1 fds=12:41 
1631268063037574239 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=58 
1631268063037576258 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631268063037595053 apache2 sendto > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=13 tuple=NULL 
1631268063037609119 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631268063037611067 apache2 poll > fds=12:431 timeout=1471228928 
1631268063037611469 mysqld poll < res=1 fds=41:41 
1631268063037612672 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037613985 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631268063037614846 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=9 
1631268063037615876 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631268063037631209 mysqld access > mode=0(F_OK) 
1631268063037638294 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268063037660409 mysqld sendto > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=11 tuple=NULL 
1631268063037674455 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631268063037678333 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063037679187 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037679719 mysqld poll > fds=41:43 timeout=28800000 
1631268063037711463 apache2 poll < res=1 fds=12:41 
1631268063037712631 apache2 recvfrom > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=47 
1631268063037714691 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631268063037738835 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268063037743991 apache2 socket < fd=13(<4>) 
1631268063037744289 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631268063037744589 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063037744706 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631268063037744855 apache2 fcntl < res=0(<f>/dev/null) 
1631268063037744995 apache2 connect > fd=13(<4>) 
1631268063037770389 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:60504->127.0.0.1:3306 
1631268063037771337 apache2 poll > fds=13:435 timeout=60000 
1631268063037771701 mysqld poll < res=1 fds=20:41 
1631268063037772133 apache2 poll < res=1 fds=13:44 
1631268063037772387 apache2 getsockopt >
1631268063037772438 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268063037772708 mysqld fcntl < res=2(<p>pipe:[368810612]) 
1631268063037772857 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037772965 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037772984 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268063037773169 mysqld accept >
1631268063037773474 apache2 fcntl > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037773678 apache2 fcntl < res=0(<f>/dev/null) 
1631268063037774815 apache2 setsockopt >
1631268063037775312 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063037775633 apache2 setsockopt >
1631268063037776034 mysqld accept < fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) tuple=127.0.0.1:60504->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268063037776076 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063037776456 mysqld fcntl > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268063037776607 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037776724 mysqld fcntl > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063037776837 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037776883 apache2 poll > fds=13:431 timeout=1471228928 
1631268063037776979 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037777063 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037777176 mysqld fcntl > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063037777274 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037786564 mysqld fcntl > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063037786770 mysqld fcntl < res=0(<f>/dev/null) 
1631268063037786932 mysqld setsockopt >
1631268063037787576 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268063037787839 mysqld setsockopt >
1631268063037788105 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063037788529 mysqld futex > addr=55C85FAC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268063037791259 mysqld futex < res=1 
1631268063037791544 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268063037793490 mysqld futex < res=0 
1631268063037794877 mysqld futex > addr=55C85FABEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268063037795243 mysqld futex < res=0 
1631268063037795973 mysqld gettid >
1631268063037796411 mysqld gettid <
1631268063037798460 mysqld getpeername >
1631268063037799895 mysqld getpeername <
1631268063037803647 mysqld setsockopt >
1631268063037804465 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063037806919 mysqld sendto > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=102 tuple=NULL 
1631268063037839641 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEArAAAAGpGXihJdjlXAP/3LQIAP6AVAAAAAAAAAAAAACpqV1gyLjJRfko2bAA= 
1631268063037840638 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063037841258 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037841877 mysqld poll > fds=74:43 timeout=10000 
1631268063037875566 apache2 poll < res=1 fds=13:41 
1631268063037876735 apache2 recvfrom > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063037878212 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268063037880106 apache2 poll > fds=13:431 timeout=1471228928 
1631268063037880760 apache2 poll < res=1 fds=13:41 
1631268063037880940 apache2 recvfrom > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=102 
1631268063037882210 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQCsAAAAakZeKEl2OVcA//ctAgA/oBUAAAAAAAAAAAAAKmpXWDIuMlF+SjZsAG15c3E= tuple=NULL 
1631268063037887201 apache2 sendto > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=110 tuple=NULL 
1631268063037900530 mysqld poll < res=1 fds=74:41 
1631268063037901157 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063037901274 apache2 sendto < res=110 data=agAAAY2iCwAAAADAIQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABQEDyoX3uCYbH2aMs0pQSdECi6cAmR2d2EAbXlzcWxfbmF0aXZlX3A= 
1631268063037901983 mysqld recvfrom < res=4 data=agAAAQ== tuple=NULL 
1631268063037902415 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=106 
1631268063037902537 apache2 poll > fds=13:431 timeout=1471228928 
1631268063037903228 mysqld recvfrom < res=106 data=jaILAAAAAMAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFAQPKhfe4JhsfZoyzSlBJ0QKLpwCZHZ3YQBteXNxbF9uYXRpdmVfcGFzc3c= tuple=NULL 
1631268063037909704 mysqld access > mode=0(F_OK) 
1631268063037914711 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268063037916777 mysqld sendto > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=11 tuple=NULL 
1631268063037925859 mysqld sendto < res=11 data=BwAAAgAAAAIAAAA= 
1631268063037928010 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063037928516 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063037928873 mysqld poll > fds=74:43 timeout=28800000 
1631268063037981396 apache2 poll < res=1 fds=13:41 
1631268063037982573 apache2 recvfrom > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063037984057 apache2 recvfrom < res=4 data=BwAAAg== tuple=NULL 
1631268063037985756 apache2 poll > fds=13:431 timeout=1471228928 
1631268063037986445 apache2 poll < res=1 fds=13:41 
1631268063037986627 apache2 recvfrom > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=102 
1631268063037987602 apache2 recvfrom < res=7 data=AAAAAgAAAA== tuple=NULL 
1631268063038003821 apache2 nanosleep > interval=0(0s) 
1631268063038059169 apache2 nanosleep < res=0 
1631268063038080323 apache2 chdir >
1631268063038082213 apache2 chdir < res=0 path=/ 
1631268063038086754 apache2 sendto > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) size=5 tuple=NULL 
1631268063038100268 mysqld poll < res=1 fds=41:41 
1631268063038100590 apache2 sendto < res=5 data=AQAAAAE= 
1631268063038101195 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=4 
1631268063038102240 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268063038102254 apache2 close > fd=12(<4t>127.0.0.1:60502->127.0.0.1:3306) 
1631268063038102900 mysqld recvfrom > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) size=1 
1631268063038103009 apache2 close < res=0 
1631268063038103557 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268063038106315 mysqld shutdown > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268063038116117 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063038118475 apache2 mmap < res=7F6034236000 vm_size=374428 vm_rss=13772 vm_swap=0 
1631268063038121372 mysqld shutdown < res=0 
1631268063038121849 mysqld close > fd=41(<4t>127.0.0.1:60502->127.0.0.1:3306) 
1631268063038122223 mysqld close < res=0 
1631268063038124177 apache2 setitimer >
1631268063038124628 apache2 setitimer <
1631268063038136719 mysqld futex > addr=55C85FAC1364 op=128(FUTEX_PRIVATE_FLAG) val=337 
1631268063038145595 apache2 pwrite > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) size=65 pos=0 
1631268063038157690 apache2 pwrite < res=65 data=ZHZ3YXxhOjA6e31zZXNzaW9uX3Rva2VufHM6MzI6ImEzMDY1NDgzYzQxY2E4YTM2NjM2NWFjMTgwY2ZjYmNkIjs= 
1631268063038158434 apache2 close > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) 
1631268063038158745 apache2 close < res=0 
1631268063038165499 apache2 sendto > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) size=5 tuple=NULL 
1631268063038176374 mysqld poll < res=1 fds=74:41 
1631268063038176791 apache2 sendto < res=5 data=AQAAAAE= 
1631268063038176826 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=4 
1631268063038177356 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268063038177697 apache2 close > fd=13(<4t>127.0.0.1:60504->127.0.0.1:3306) 
1631268063038177811 mysqld recvfrom > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) size=1 
1631268063038177918 apache2 close < res=0 
1631268063038178295 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268063038180995 mysqld shutdown > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268063038191985 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.I1y8sF (deleted)) cmd=8(F_SETLK) 
1631268063038192277 mysqld shutdown < res=0 
1631268063038192656 mysqld close > fd=74(<4t>127.0.0.1:60504->127.0.0.1:3306) 
1631268063038193023 mysqld close < res=0 
1631268063038193486 apache2 fcntl < res=0(<f>/dev/null) 
1631268063038199094 apache2 setitimer >
1631268063038199397 apache2 setitimer <
1631268063038204006 mysqld futex > addr=55C85FAC1364 op=128(FUTEX_PRIVATE_FLAG) val=338 
1631268063038205146 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063038206681 apache2 mmap < res=7F6034234000 vm_size=374436 vm_rss=13772 vm_swap=0 
1631268063038215968 apache2 brk > addr=55C5E4480000 
1631268063038216915 apache2 brk < res=55C5E4480000 vm_size=374584 vm_rss=13772 vm_swap=0 
1631268063038220267 apache2 mmap > addr=0 length=135168 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063038220845 apache2 mmap < res=7F6034213000 vm_size=374716 vm_rss=13772 vm_swap=0 
1631268063038305814 apache2 munmap > addr=7F6034213000 length=135168 
1631268063038311940 apache2 munmap < res=0 vm_size=374584 vm_rss=14736 vm_swap=0 
1631268063038312528 apache2 brk > addr=55C5E445E000 
1631268063038320272 apache2 brk < res=55C5E445E000 vm_size=374448 vm_rss=14604 vm_swap=0 
1631268063038326468 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063038327443 apache2 mmap < res=7F6034232000 vm_size=374456 vm_rss=14604 vm_swap=0 
1631268063038335950 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063038336455 apache2 mmap < res=7F6034230000 vm_size=374464 vm_rss=14604 vm_swap=0 
1631268063038340979 apache2 read > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=8000 
1631268063038342303 apache2 read < res=-11(EAGAIN) data= 
1631268063038345646 apache2 writev > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=1192 
1631268063038370758 apache2 writev < res=1192 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAxOjAzIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268063038383761 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=194 
1631268063038389615 apache2 write < res=194 data=MTkyLjE2OC4xNi4xNiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAxOjAzICswMDAwXSAiR0VUIC9sb2dpbi5waHAgSFRUUC8xLjEiIDIwMCAxMTk= 
1631268063038390638 apache2 times >
1631268063038391586 apache2 times <
1631268063038397608 apache2 poll > fds=10:41 timeout=5000 
1631268063051633339 apache2 poll < res=1 fds=10:41 
1631268063051636155 apache2 read > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=8000 
1631268063051639144 apache2 read < res=400 data=R0VUIC9kdndhL2Nzcy9sb2dpbi5jc3MgSFRUUC8xLjENCkhvc3Q6IDM2NjgzYzVmYzMxY2VhMmINCkNvbm5lY3Rpb246IGtlZXAtYWxpdmU= 
1631268063051692281 apache2 stat >
1631268063051701308 apache2 stat < res=0 path=/var/www/html/dvwa/css/login.css 
1631268063051722232 apache2 open >
1631268063051729767 apache2 open < fd=11(<f>/var/www/html/dvwa/css/login.css) name=/var/www/html/dvwa/css/login.css flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000FA 
1631268063051737980 apache2 mmap > addr=0 length=842 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/css/login.css) offset=0 
1631268063051742255 apache2 mmap < res=7F603439B000 vm_size=374468 vm_rss=14604 vm_swap=0 
1631268063051747728 apache2 brk > addr=55C5E4480000 
1631268063051750021 apache2 brk < res=55C5E4480000 vm_size=374604 vm_rss=14604 vm_swap=0 
1631268063051754532 apache2 brk > addr=55C5E44C0000 
1631268063051754948 apache2 brk < res=55C5E44C0000 vm_size=374860 vm_rss=14604 vm_swap=0 
1631268063051769587 apache2 accept < fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) tuple=192.168.16.16:60246->192.168.16.17:80 queuepct=0 queuelen=0 queuemax=511 
1631268063051784638 apache2 getsockname >
1631268063051785504 apache2 getsockname <
1631268063051791158 apache2 fcntl > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) cmd=4(F_GETFL) 
1631268063051791481 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063051791635 apache2 fcntl > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) cmd=5(F_SETFL) 
1631268063051791826 apache2 fcntl < res=0(<f>/dev/null) 
1631268063051796278 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063051798584 apache2 mmap < res=7F603424C000 vm_size=374020 vm_rss=9100 vm_swap=0 
1631268063051807695 apache2 munmap > addr=7F603439B000 length=842 
1631268063051807859 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063051808545 apache2 mmap < res=7F603424A000 vm_size=374028 vm_rss=9100 vm_swap=0 
1631268063051810066 apache2 read > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=8000 
1631268063051810934 apache2 munmap < res=0 vm_size=374856 vm_rss=14824 vm_swap=0 
1631268063051812765 apache2 read < res=454 data=R0VUIC9kdndhL2ltYWdlcy9sb2dpbl9sb2dvLnBuZyBIVFRQLzEuMQ0KSG9zdDogMzY2ODNjNWZjMzFjZWEyYg0KQ29ubmVjdGlvbjoga2U= 
1631268063051833345 apache2 brk > addr=55C5E4480000 
1631268063051838013 apache2 brk < res=55C5E4480000 vm_size=374600 vm_rss=14812 vm_swap=0 
1631268063051838423 apache2 brk > addr=55C5E445E000 
1631268063051845254 apache2 brk < res=55C5E445E000 vm_size=374464 vm_rss=14680 vm_swap=0 
1631268063051847651 apache2 stat >
1631268063051853911 apache2 stat < res=0 path=/var/www/html/dvwa/images/login_logo.png 
1631268063051854849 apache2 read > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=8000 
1631268063051855884 apache2 read < res=-11(EAGAIN) data= 
1631268063051857283 apache2 writev > fd=10(<4t>192.168.16.16:60244->192.168.16.17:80) size=741 
1631268063051861215 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063051862287 apache2 mmap < res=7F6034248000 vm_size=374036 vm_rss=9100 vm_swap=0 
1631268063051881790 apache2 writev < res=741 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAxOjAzIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268063051887357 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=234 
1631268063051893230 apache2 write < res=234 data=MTkyLjE2OC4xNi4xNiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAxOjAzICswMDAwXSAiR0VUIC9kdndhL2Nzcy9sb2dpbi5jc3MgSFRUUC8xLjE= 
1631268063051894106 apache2 times >
1631268063051895865 apache2 times <
1631268063051896227 apache2 close > fd=11(<f>/var/www/html/dvwa/css/login.css) 
1631268063051896598 apache2 close < res=0 
1631268063051897555 apache2 open >
1631268063051900536 apache2 poll > fds=10:41 timeout=5000 
1631268063051902807 apache2 open < fd=11(<f>/var/www/html/dvwa/images/login_logo.png) name=/var/www/html/dvwa/images/login_logo.png flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000FA 
1631268063051912241 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063051913319 apache2 mmap < res=7F6034246000 vm_size=374044 vm_rss=9100 vm_swap=0 
1631268063051919350 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063051919855 apache2 mmap < res=7F6034244000 vm_size=374052 vm_rss=9100 vm_swap=0 
1631268063051922957 apache2 mmap > addr=0 length=9088 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/images/login_logo.png) offset=0 
1631268063051924666 apache2 mmap < res=7F6034241000 vm_size=374064 vm_rss=9100 vm_swap=0 
1631268063051926461 apache2 writev > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=9375 
1631268063051988935 apache2 writev < res=9375 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAxOjAzIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268063051991526 apache2 munmap > addr=7F6034241000 length=9088 
1631268063051994203 apache2 munmap < res=0 vm_size=374052 vm_rss=10272 vm_swap=0 
1631268063052008127 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=243 
1631268063052012355 apache2 write < res=243 data=MTkyLjE2OC4xNi4xNiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAxOjAzICswMDAwXSAiR0VUIC9kdndhL2ltYWdlcy9sb2dpbl9sb2dvLnBuZyA= 
1631268063052013118 apache2 times >
1631268063052014077 apache2 times <
1631268063052014432 apache2 close > fd=11(<f>/var/www/html/dvwa/images/login_logo.png) 
1631268063052014776 apache2 close < res=0 
1631268063052017782 apache2 read > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=8000 
1631268063052018616 apache2 read < res=-11(EAGAIN) data= 
1631268063052023992 apache2 poll > fds=10:41 timeout=5000 
1631268063071319075 apache2 poll < res=1 fds=10:41 
1631268063071321708 apache2 read > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=8000 
1631268063071323987 apache2 read < res=439 data=R0VUIC9mYXZpY29uLmljbyBIVFRQLzEuMQ0KSG9zdDogMzY2ODNjNWZjMzFjZWEyYg0KQ29ubmVjdGlvbjoga2VlcC1hbGl2ZQ0KVXNlci0= 
1631268063071358382 apache2 stat >
1631268063071366102 apache2 stat < res=0 path=/var/www/html/favicon.ico 
1631268063071384748 apache2 open >
1631268063071391956 apache2 open < fd=11(<f>/var/www/html/favicon.ico) name=/var/www/html/favicon.ico flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000FA 
1631268063071424289 apache2 read > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=8000 
1631268063071425280 apache2 read < res=-11(EAGAIN) data= 
1631268063071426534 apache2 mmap > addr=0 length=1406 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/favicon.ico) offset=0 
1631268063071430319 apache2 mmap < res=7F603439B000 vm_size=374056 vm_rss=10272 vm_swap=0 
1631268063071431243 apache2 writev > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=1706 
1631268063071457319 apache2 writev < res=1706 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAxOjAzIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268063071458624 apache2 munmap > addr=7F603439B000 length=1406 
1631268063071461140 apache2 munmap < res=0 vm_size=374052 vm_rss=10336 vm_swap=0 
1631268063071465157 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=228 
1631268063071471630 apache2 write < res=228 data=MTkyLjE2OC4xNi4xNiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAxOjAzICswMDAwXSAiR0VUIC9mYXZpY29uLmljbyBIVFRQLzEuMSIgMjAwIDE= 
1631268063071472478 apache2 times >
1631268063071473498 apache2 times <
1631268063071474364 apache2 close > fd=11(<f>/var/www/html/favicon.ico) 
1631268063071474655 apache2 close < res=0 
1631268063071478154 apache2 poll > fds=10:41 timeout=5000 
1631268063122185185 mysqld io_getevents <
1631268063122188217 mysqld io_getevents >
1631268063132543855 apache2 select < res=0 
1631268063132547502 apache2 write > fd=5(<p>pipe:[368820295]) size=1 
1631268063132549458 apache2 write < res=1 data=IQ== 
1631268063132553265 apache2 socket > domain=2(AF_INET) type=524289 proto=0 
1631268063132561748 apache2 socket < fd=9(<4>) 
1631268063132562530 apache2 fcntl > fd=9(<4>) cmd=4(F_GETFL) 
1631268063132563024 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063132563136 apache2 fcntl > fd=9(<4>) cmd=5(F_SETFL) 
1631268063132563290 apache2 fcntl < res=0(<f>/dev/null) 
1631268063132563676 apache2 connect > fd=9(<4>) 
1631268063132594007 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:37668->0.0.0.0:80 
1631268063132595566 apache2 poll > fds=9:44 timeout=3000 
1631268063132596426 apache2 poll < res=1 fds=9:44 
1631268063132596727 apache2 getsockopt >
1631268063132597497 apache2 getsockopt < res=0 fd=9(<4t>127.0.0.1:37668->0.0.0.0:80) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268063132599629 apache2 write > fd=9(<4t>127.0.0.1:37668->0.0.0.0:80) size=86 
1631268063132623577 apache2 write < res=86 data=T1BUSU9OUyAqIEhUVFAvMS4wDQpVc2VyLUFnZW50OiBBcGFjaGUvMi40LjI1IChEZWJpYW4pIChpbnRlcm5hbCBkdW1teSBjb25uZWN0aW8= 
1631268063132624509 apache2 close > fd=9(<4t>127.0.0.1:37668->0.0.0.0:80) 
1631268063132625007 apache2 close < res=0 
1631268063132625145 apache2 accept < fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) tuple=127.0.0.1:37668->127.0.0.1:80 queuepct=0 queuelen=0 queuemax=511 
1631268063132633033 apache2 wait4 >
1631268063132640146 apache2 getsockname >
1631268063132640968 apache2 getsockname <
1631268063132642156 apache2 wait4 <
1631268063132644502 apache2 wait4 >
1631268063132646128 apache2 wait4 <
1631268063132646385 apache2 select >
1631268063132647676 apache2 fcntl > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) cmd=4(F_GETFL) 
1631268063132647985 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063132648121 apache2 fcntl > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) cmd=5(F_SETFL) 
1631268063132648283 apache2 fcntl < res=0(<f>/dev/null) 
1631268063132652736 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063132654949 apache2 mmap < res=7F603424C000 vm_size=374020 vm_rss=9100 vm_swap=0 
1631268063132665129 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063132665785 apache2 mmap < res=7F603424A000 vm_size=374028 vm_rss=9100 vm_swap=0 
1631268063132667535 apache2 read > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) size=8000 
1631268063132669812 apache2 read < res=86 data=T1BUSU9OUyAqIEhUVFAvMS4wDQpVc2VyLUFnZW50OiBBcGFjaGUvMi40LjI1IChEZWJpYW4pIChpbnRlcm5hbCBkdW1teSBjb25uZWN0aW8= 
1631268063132711807 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063132712691 apache2 mmap < res=7F6034248000 vm_size=374036 vm_rss=9100 vm_swap=0 
1631268063132722209 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063132722783 apache2 mmap < res=7F6034246000 vm_size=374044 vm_rss=9100 vm_swap=0 
1631268063132726471 apache2 writev > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) size=126 
1631268063132746137 apache2 writev < res=126 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAxOjAzIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268063132760346 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=129 
1631268063132771409 apache2 write < res=129 data=MTI3LjAuMC4xIC0gLSBbMTAvU2VwLzIwMjE6MTA6MDE6MDMgKzAwMDBdICJPUFRJT05TICogSFRUUC8xLjAiIDIwMCAxMjYgIi0iICJBcGE= 
1631268063132772281 apache2 times >
1631268063132773403 apache2 times <
1631268063132777135 apache2 shutdown > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) how=1(SHUT_WR) 
1631268063132777842 apache2 shutdown < res=-107(ENOTCONN) 
1631268063132778375 apache2 close > fd=10(<4t>127.0.0.1:37668->127.0.0.1:80) 
1631268063132778719 apache2 close < res=0 
1631268063132782267 apache2 read > fd=4(<p>pipe:[368820295]) size=1 
1631268063132783430 apache2 read < res=1 data=IQ== 
1631268063132784993 apache2 close > fd=9 
1631268063132785241 apache2 close < res=0 
1631268063133323988 apache2 munmap > addr=7F601D6EF000 length=67108864 
1631268063133332631 apache2 munmap < res=0 vm_size=308508 vm_rss=10732 vm_swap=0 
1631268063133334999 apache2 close > fd=8(<f>/tmp/.ZendSem.I1y8sF (deleted)) 
1631268063133335579 apache2 close < res=0 
1631268063133459916 apache2 munmap > addr=7F6022068000 length=2126312 
1631268063133466924 apache2 munmap < res=0 vm_size=306428 vm_rss=11628 vm_swap=0 
1631268063133467677 apache2 munmap > addr=7F6021E52000 length=2183192 
1631268063133472603 apache2 munmap < res=0 vm_size=304292 vm_rss=11540 vm_swap=0 
1631268063133473045 apache2 munmap > addr=7F6021C13000 length=2352488 
1631268063133479167 apache2 munmap < res=0 vm_size=301992 vm_rss=11340 vm_swap=0 
1631268063133479591 apache2 munmap > addr=7F6021903000 length=3208448 
1631268063133484997 apache2 munmap < res=0 vm_size=298856 vm_rss=11176 vm_swap=0 
1631268063133485387 apache2 munmap > addr=7F60216EF000 length=2175160 
1631268063133489853 apache2 munmap < res=0 vm_size=296728 vm_rss=11104 vm_swap=0 
1631268063133504599 apache2 munmap > addr=7F6022270000 length=2142720 
1631268063133509804 apache2 munmap < res=0 vm_size=294632 vm_rss=11088 vm_swap=0 
1631268063133521487 apache2 munmap > addr=7F602247C000 length=2130472 
1631268063133525883 apache2 munmap < res=0 vm_size=292548 vm_rss=11080 vm_swap=0 
1631268063133535235 apache2 munmap > addr=7F6022685000 length=2126032 
1631268063133540403 apache2 munmap < res=0 vm_size=290468 vm_rss=11072 vm_swap=0 
1631268063133548672 apache2 munmap > addr=7F602288D000 length=2113776 
1631268063133552480 apache2 munmap < res=0 vm_size=288400 vm_rss=11064 vm_swap=0 
1631268063133560497 apache2 munmap > addr=7F6022A92000 length=2109680 
1631268063133564568 apache2 munmap < res=0 vm_size=286336 vm_rss=11056 vm_swap=0 
1631268063133572048 apache2 munmap > addr=7F6022C96000 length=2105552 
1631268063133575711 apache2 munmap < res=0 vm_size=284276 vm_rss=11048 vm_swap=0 
1631268063133583293 apache2 munmap > addr=7F6022E99000 length=2113744 
1631268063133586968 apache2 munmap < res=0 vm_size=282208 vm_rss=11040 vm_swap=0 
1631268063133596726 apache2 munmap > addr=7F602309E000 length=2183504 
1631268063133600967 apache2 munmap < res=0 vm_size=280072 vm_rss=11028 vm_swap=0 
1631268063133609704 apache2 munmap > addr=7F60232B4000 length=2150936 
1631268063133614155 apache2 munmap < res=0 vm_size=277968 vm_rss=11020 vm_swap=0 
1631268063133622078 apache2 munmap > addr=7F60234C2000 length=2109656 
1631268063133626256 apache2 munmap < res=0 vm_size=275904 vm_rss=11012 vm_swap=0 
1631268063133845811 apache2 munmap > addr=7F6023D4B000 length=2126152 
1631268063133851064 apache2 munmap < res=0 vm_size=273824 vm_rss=15116 vm_swap=0 
1631268063133851652 apache2 munmap > addr=7F6023B13000 length=2322976 
1631268063133856685 apache2 munmap < res=0 vm_size=271552 vm_rss=14980 vm_swap=0 
1631268063133857090 apache2 munmap > addr=7F60238F0000 length=2236808 
1631268063133861880 apache2 munmap < res=0 vm_size=269364 vm_rss=14848 vm_swap=0 
1631268063133862226 apache2 munmap > addr=7F60236C6000 length=2267936 
1631268063133867642 apache2 munmap < res=0 vm_size=267148 vm_rss=14724 vm_swap=0 
1631268063133875660 apache2 munmap > addr=7F6023F53000 length=2130320 
1631268063133879871 apache2 munmap < res=0 vm_size=265064 vm_rss=14688 vm_swap=0 
1631268063133894405 apache2 munmap > addr=7F602415C000 length=2381440 
1631268063133900579 apache2 munmap < res=0 vm_size=262736 vm_rss=14672 vm_swap=0 
1631268063133916716 apache2 munmap > addr=7F60243A2000 length=2236896 
1631268063133921857 apache2 munmap < res=0 vm_size=260548 vm_rss=14588 vm_swap=0 
1631268063134047837 apache2 munmap > addr=7F6026F1A000 length=2138688 
1631268063134054072 apache2 munmap < res=0 vm_size=258456 vm_rss=15724 vm_swap=0 
1631268063134054683 apache2 munmap > addr=7F6026CE9000 length=2294064 
1631268063134059952 apache2 munmap < res=0 vm_size=256212 vm_rss=15584 vm_swap=0 
1631268063134060381 apache2 munmap > addr=7F6026A9E000 length=2401248 
1631268063134065840 apache2 munmap < res=0 vm_size=253864 vm_rss=15440 vm_swap=0 
1631268063134066455 apache2 munmap > addr=7F602684D000 length=2427528 
1631268063134071968 apache2 munmap < res=0 vm_size=251492 vm_rss=15300 vm_swap=0 
1631268063134073745 apache2 munmap > addr=7F6026573000 length=2988384 
1631268063134080057 apache2 munmap < res=0 vm_size=248572 vm_rss=15044 vm_swap=0 
1631268063134080478 apache2 munmap > addr=7F6026340000 length=2302456 
1631268063134086118 apache2 munmap < res=0 vm_size=246320 vm_rss=14912 vm_swap=0 
1631268063134086654 apache2 munmap > addr=7F602613C000 length=2109608 
1631268063134090043 apache2 munmap < res=0 vm_size=244256 vm_rss=14892 vm_swap=0 
1631268063134090363 apache2 munmap > addr=7F6025F30000 length=2143528 
1631268063134094560 apache2 munmap < res=0 vm_size=242160 vm_rss=14844 vm_swap=0 
1631268063134094961 apache2 munmap > addr=7F6025D2C000 length=2109456 
1631268063134098565 apache2 munmap < res=0 vm_size=240096 vm_rss=14824 vm_swap=0 
1631268063134098884 apache2 munmap > addr=7F6025B1D000 length=2154920 
1631268063134103004 apache2 munmap < res=0 vm_size=237988 vm_rss=14768 vm_swap=0 
1631268063134103400 apache2 munmap > addr=7F6025902000 length=2204648 
1631268063134108469 apache2 munmap < res=0 vm_size=235832 vm_rss=14656 vm_swap=0 
1631268063134108856 apache2 munmap > addr=7F6025569000 length=3771208 
1631268063134118747 apache2 munmap < res=0 vm_size=232148 vm_rss=14020 vm_swap=0 
1631268063134119193 apache2 munmap > addr=7F6025304000 length=2507952 
1631268063134125765 apache2 munmap < res=0 vm_size=229696 vm_rss=13744 vm_swap=0 
1631268063134126135 apache2 munmap > addr=7F60250D0000 length=2306096 
1631268063134130169 apache2 munmap < res=0 vm_size=227440 vm_rss=13676 vm_swap=0 
1631268063134130535 apache2 munmap > addr=7F6024EBD000 length=2171592 
1631268063134134290 apache2 munmap < res=0 vm_size=225316 vm_rss=13604 vm_swap=0 
1631268063134134646 apache2 munmap > addr=7F6024A51000 length=2311792 
1631268063134139090 apache2 munmap < res=0 vm_size=223056 vm_rss=13472 vm_swap=0 
1631268063134139523 apache2 munmap > addr=7F6024C86000 length=2319552 
1631268063134144360 apache2 munmap < res=0 vm_size=220788 vm_rss=13332 vm_swap=0 
1631268063134144732 apache2 munmap > addr=7F60247CE000 length=2632576 
1631268063134149842 apache2 munmap < res=0 vm_size=218216 vm_rss=13196 vm_swap=0 
1631268063134150223 apache2 munmap > addr=7F60245C5000 length=2131560 
1631268063134153828 apache2 munmap < res=0 vm_size=216132 vm_rss=13160 vm_swap=0 
1631268063134162155 apache2 munmap > addr=7F6027125000 length=2126312 
1631268063134166922 apache2 munmap < res=0 vm_size=214052 vm_rss=13128 vm_swap=0 
1631268063134182554 apache2 munmap > addr=7F602732D000 length=2238728 
1631268063134188145 apache2 munmap < res=0 vm_size=211864 vm_rss=13044 vm_swap=0 
1631268063134194235 apache2 munmap > addr=7F6027550000 length=2134248 
1631268063134198847 apache2 munmap < res=0 vm_size=209776 vm_rss=13000 vm_swap=0 
1631268063134206095 apache2 munmap > addr=7F602775A000 length=2138392 
1631268063134210592 apache2 munmap < res=0 vm_size=207684 vm_rss=12956 vm_swap=0 
1631268063134215982 apache2 munmap > addr=7F6027965000 length=2109648 
1631268063134220479 apache2 munmap < res=0 vm_size=205620 vm_rss=12936 vm_swap=0 
1631268063134289744 apache2 munmap > addr=7F6029BDB000 length=2199768 
1631268063134296073 apache2 munmap < res=0 vm_size=203468 vm_rss=13512 vm_swap=0 
1631268063134296655 apache2 munmap > addr=7F6029974000 length=2517896 
1631268063134302889 apache2 munmap < res=0 vm_size=201008 vm_rss=13300 vm_swap=0 
1631268063134303317 apache2 munmap > addr=7F6029422000 length=2168016 
1631268063134307841 apache2 munmap < res=0 vm_size=198888 vm_rss=13232 vm_swap=0 
1631268063134308239 apache2 munmap > addr=7F6029634000 length=3407224 
1631268063134314550 apache2 munmap < res=0 vm_size=195560 vm_rss=13016 vm_swap=0 
1631268063134314953 apache2 munmap > addr=7F6028D23000 length=2494200 
1631268063134320238 apache2 munmap < res=0 vm_size=193124 vm_rss=12884 vm_swap=0 
1631268063134320579 apache2 munmap > addr=7F6028836000 length=2348648 
1631268063134325467 apache2 munmap < res=0 vm_size=190828 vm_rss=12744 vm_swap=0 
1631268063134325835 apache2 munmap > addr=7F6028A74000 length=2811792 
1631268063134331639 apache2 munmap < res=0 vm_size=188080 vm_rss=12548 vm_swap=0 
1631268063134332018 apache2 munmap > addr=7F60291EF000 length=2301968 
1631268063134336705 apache2 munmap < res=0 vm_size=185828 vm_rss=12416 vm_swap=0 
1631268063134337091 apache2 munmap > addr=7F60285BF000 length=2581488 
1631268063134342507 apache2 munmap < res=0 vm_size=183304 vm_rss=12276 vm_swap=0 
1631268063134342893 apache2 munmap > addr=7F6028F84000 length=2531352 
1631268063134347312 apache2 munmap < res=0 vm_size=180828 vm_rss=12148 vm_swap=0 
1631268063134347714 apache2 munmap > addr=7F6028397000 length=2258056 
1631268063134352434 apache2 munmap < res=0 vm_size=178620 vm_rss=12024 vm_swap=0 
1631268063134352809 apache2 munmap > addr=7F6028189000 length=2153448 
1631268063134356795 apache2 munmap < res=0 vm_size=176516 vm_rss=11968 vm_swap=0 
1631268063134357133 apache2 munmap > addr=7F6027F85000 length=2109744 
1631268063134360651 apache2 munmap < res=0 vm_size=174452 vm_rss=11948 vm_swap=0 
1631268063134360944 apache2 munmap > addr=7F6027D7F000 length=2117872 
1631268063134364456 apache2 munmap < res=0 vm_size=172380 vm_rss=11920 vm_swap=0 
1631268063134364865 apache2 munmap > addr=7F6027B69000 length=2183248 
1631268063134369498 apache2 munmap < res=0 vm_size=170244 vm_rss=11840 vm_swap=0 
1631268063134376674 apache2 munmap > addr=7F6029DF5000 length=2154704 
1631268063134380897 apache2 munmap < res=0 vm_size=168136 vm_rss=11788 vm_swap=0 
1631268063134387385 apache2 munmap > addr=7F602A004000 length=5264896 
1631268063134392569 apache2 munmap < res=0 vm_size=162992 vm_rss=11716 vm_swap=0 
1631268063134398573 apache2 munmap > addr=7F602A50A000 length=2158896 
1631268063134402980 apache2 munmap < res=0 vm_size=160880 vm_rss=11652 vm_swap=0 
1631268063134417499 apache2 munmap > addr=7F602A71A000 length=2292264 
1631268063134422449 apache2 munmap < res=0 vm_size=158640 vm_rss=11564 vm_swap=0 
1631268063134427461 apache2 munmap > addr=7F602A94A000 length=2109648 
1631268063134431280 apache2 munmap < res=0 vm_size=156576 vm_rss=11548 vm_swap=0 
1631268063134436324 apache2 munmap > addr=7F602AB4E000 length=2131256 
1631268063134440678 apache2 munmap < res=0 vm_size=154492 vm_rss=11512 vm_swap=0 
1631268063134447561 apache2 munmap > addr=7F602AD57000 length=2146944 
1631268063134451583 apache2 munmap < res=0 vm_size=152392 vm_rss=11456 vm_swap=0 
1631268063134462634 apache2 munmap > addr=7F602AF64000 length=2204928 
1631268063134467810 apache2 munmap < res=0 vm_size=150236 vm_rss=11344 vm_swap=0 
1631268063134479128 apache2 munmap > addr=7F602B17F000 length=2385792 
1631268063134485822 apache2 munmap < res=0 vm_size=147904 vm_rss=11248 vm_swap=0 
1631268063134690860 apache2 munmap > addr=7F602B3C6000 length=2332344 
1631268063134699170 apache2 munmap < res=0 vm_size=145624 vm_rss=12156 vm_swap=0 
1631268063134735841 apache2 munmap > addr=7F6034268000 length=151552 
1631268063134742048 apache2 munmap < res=0 vm_size=145476 vm_rss=12048 vm_swap=0 
1631268063134750719 apache2 munmap > addr=7F602B600000 length=2097152 
1631268063134768443 apache2 munmap < res=0 vm_size=143428 vm_rss=10000 vm_swap=0 
1631268063134773177 apache2 munmap > addr=7F603428D000 length=323584 
1631268063134775364 apache2 munmap < res=0 vm_size=143112 vm_rss=9996 vm_swap=0 
1631268063134777915 apache2 munmap > addr=7F6034252000 length=8192 
1631268063134779848 apache2 munmap < res=0 vm_size=143104 vm_rss=9992 vm_swap=0 
1631268063134780063 apache2 munmap > addr=7F603424E000 length=8192 
1631268063134781646 apache2 munmap < res=0 vm_size=143096 vm_rss=9988 vm_swap=0 
1631268063134781808 apache2 munmap > addr=7F6034250000 length=8192 
1631268063134782877 apache2 munmap < res=0 vm_size=143088 vm_rss=9984 vm_swap=0 
1631268063134783031 apache2 munmap > addr=7F603424A000 length=8192 
1631268063134784248 apache2 munmap < res=0 vm_size=143080 vm_rss=9980 vm_swap=0 
1631268063134784409 apache2 munmap > addr=7F6034246000 length=8192 
1631268063134785825 apache2 munmap < res=0 vm_size=143072 vm_rss=9976 vm_swap=0 
1631268063134785966 apache2 munmap > addr=7F603424C000 length=8192 
1631268063134786933 apache2 munmap < res=0 vm_size=143064 vm_rss=9968 vm_swap=0 
1631268063134787081 apache2 munmap > addr=7F6034248000 length=8192 
1631268063134788725 apache2 munmap < res=0 vm_size=143056 vm_rss=9964 vm_swap=0 
1631268063134791291 apache2 close > fd=5(<p>pipe:[368820295]) 
1631268063134791689 apache2 close < res=0 
1631268063134791921 apache2 close > fd=4(<p>pipe:[368820295]) 
1631268063134792075 apache2 close < res=0 
1631268063134863600 apache2 futex > addr=7F602F4808EC op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=2147483647 
1631268063134864128 apache2 futex < res=0 
1631268063135023789 apache2 exit_group >
1631268063135359568 apache2 procexit > status=0 
1631268063180743205 mysqld io_getevents <
1631268063180746098 mysqld io_getevents >
1631268063180751212 mysqld io_getevents <
1631268063180753034 mysqld io_getevents >
1631268063188170842 mysqld io_getevents <
1631268063188172262 mysqld io_getevents >
1631268063204354803 apache2 poll < res=0 fds= 
1631268063204358617 apache2 close > fd=10(<4t>192.168.16.7:45640->192.168.16.17:80) 
1631268063204359001 apache2 close < res=0 
1631268063204370258 apache2 read > fd=4(<p>pipe:[368820295]) size=1 
1631268063204371408 apache2 read < res=-11(EAGAIN) data= 
1631268063204376208 apache2 accept > flags=0 
1631268063206133467 apache2 poll < res=1 fds=10:41 
1631268063206135815 apache2 read > fd=10(<4t>192.168.16.16:60246->192.168.16.17:80) size=8000 
1631268063206137762 apache2 read < res=755 data=UE9TVCAvbG9naW4ucGhwIEhUVFAvMS4xDQpIb3N0OiAzNjY4M2M1ZmMzMWNlYTJiDQpDb25uZWN0aW9uOiBrZWVwLWFsaXZlDQpDb250ZW4= 
1631268063206175826 apache2 stat >
1631268063206183696 apache2 stat < res=0 path=/var/www/html/login.php 
1631268063206267844 apache2 brk > addr=55C5E443A000 
1631268063206270171 apache2 brk < res=55C5E443A000 vm_size=374240 vm_rss=10336 vm_swap=0 
1631268063206413473 apache2 brk > addr=55C5E445B000 
1631268063206414730 apache2 brk < res=55C5E445B000 vm_size=374372 vm_rss=11292 vm_swap=0 
1631268063206471227 apache2 setitimer >
1631268063206473179 apache2 setitimer <
1631268063206473590 apache2 rt_sigaction >
1631268063206473931 apache2 rt_sigaction <
1631268063206474244 apache2 rt_sigprocmask >
1631268063206474470 apache2 rt_sigprocmask <
1631268063206543535 apache2 mmap > addr=0 length=65536 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268063206545804 apache2 mmap < res=7F6034234000 vm_size=374436 vm_rss=12024 vm_swap=0 
1631268063206568383 apache2 getcwd >
1631268063206569237 apache2 getcwd < res=2 path=/ 
1631268063206569991 apache2 chdir >
1631268063206572376 apache2 chdir < res=0 path=/var/www/html 
1631268063206573891 apache2 setitimer >
1631268063206574155 apache2 setitimer <
1631268063206579099 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.I1y8sF (deleted)) cmd=8(F_SETLK) 
1631268063206581628 apache2 fcntl < res=0(<f>/dev/null) 
1631268063206600115 apache2 getcwd >
1631268063206600648 apache2 getcwd < res=14 path=/var/www/html 
1631268063206653731 apache2 open >
1631268063206663614 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) name=/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5 flags=7(O_CREAT|O_RDWR) mode=0600 dev=1000FA 
1631268063206665176 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) 
1631268063206666553 apache2 fstat < res=0 
1631268063206667003 apache2 getuid >
1631268063206667448 apache2 getuid < uid=33(www-data) 
1631268063206667910 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) operation=2(LOCK_EX) 
1631268063206669993 apache2 flock < res=0 
1631268063206670514 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) cmd=3(F_SETFD) 
1631268063206670851 apache2 fcntl < res=0(<f>/dev/null) 
1631268063206671075 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) 
1631268063206671709 apache2 fstat < res=0 
1631268063206671957 apache2 pread > fd=11(<f>/var/lib/php/sessions/sess_8t81ra66do600jffehbmt49qc5) size=65 pos=0 
1631268063206679260 apache2 pread < res=65 data=ZHZ3YXxhOjA6e31zZXNzaW9uX3Rva2VufHM6MzI6ImEzMDY1NDgzYzQxY2E4YTM2NjM2NWFjMTgwY2ZjYmNkIjs= 
1631268063206702476 apache2 access > mode=0(F_OK) 
1631268063206707720 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268063206746219 apache2 getcwd >
1631268063206746863 apache2 getcwd < res=14 path=/var/www/html 
1631268063206752036 apache2 lstat >
1631268063206757001 apache2 lstat < res=0 path=/var/www/html/hackable/uploads 
1631268063206757802 apache2 lstat >
1631268063206759965 apache2 lstat < res=0 path=/var/www/html/hackable 
1631268063206760424 apache2 lstat >
1631268063206762000 apache2 lstat < res=0 path=/var/www/html 
1631268063206762417 apache2 lstat >
1631268063206764162 apache2 lstat < res=0 path=/var/www 
1631268063206764777 apache2 lstat >
1631268063206766439 apache2 lstat < res=0 path=/var 
1631268063206774892 apache2 getcwd >
1631268063206775411 apache2 getcwd < res=14 path=/var/www/html 
1631268063206776798 apache2 lstat >
1631268063206782608 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268063206783571 apache2 lstat >
1631268063206786096 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp 
1631268063206786686 apache2 lstat >
1631268063206788113 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS 
1631268063206788589 apache2 lstat >
1631268063206789925 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib 
1631268063206790423 apache2 lstat >
1631268063206791687 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6 
1631268063206792113 apache2 lstat >
1631268063206793292 apache2 lstat < res=0 path=/var/www/html/external/phpids 
1631268063206795179 apache2 lstat >
1631268063206796486 apache2 lstat < res=0 path=/var/www/html/external 
1631268063206798380 apache2 getcwd >
1631268063206798638 apache2 getcwd < res=14 path=/var/www/html 
1631268063206799190 apache2 lstat >
1631268063206800821 apache2 lstat < res=0 path=/var/www/html/config 
1631268063206817084 apache2 open >
1631268063206823087 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000FA 
1631268063206824897 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631268063206825297 apache2 lseek < res=0 
1631268063206825938 apache2 fstat > fd=12(<f>/etc/passwd) 
1631268063206826629 apache2 fstat < res=0 
1631268063206826858 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631268063206829455 apache2 mmap < res=7F603439B000 vm_size=374440 vm_rss=13596 vm_swap=0 
1631268063206829684 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631268063206830074 apache2 lseek < res=1022 
1631268063206834485 apache2 munmap > addr=7F603439B000 length=1022 
1631268063206837219 apache2 munmap < res=0 vm_size=374436 vm_rss=13720 vm_swap=0 
1631268063206837428 apache2 close > fd=12(<f>/etc/passwd) 
1631268063206837721 apache2 close < res=0 
1631268063206841546 apache2 access > mode=2(W_OK) 
1631268063206844302 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631268063206845732 apache2 access > mode=2(W_OK) 
1631268063206846952 apache2 access < res=0 name=/var/www/html/config 
1631268063206847591 apache2 access > mode=2(W_OK) 
1631268063206849368 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268063206887030 apache2 socket > domain=10(AF_INET6) type=2 proto=0 
1631268063206892384 apache2 socket < fd=12(<6>) 
1631268063206894513 apache2 close > fd=12(<6>) 
1631268063206894720 apache2 close < res=0 
1631268063206901431 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268063206904124 apache2 socket < fd=12(<4>) 
1631268063206904422 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631268063206904697 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063206904823 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631268063206904978 apache2 fcntl < res=0(<f>/dev/null) 
1631268063206905150 apache2 connect > fd=12(<4>) 
1631268063206944144 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:60508->127.0.0.1:3306 
1631268063206945394 apache2 poll > fds=12:435 timeout=60000 
1631268063206946277 apache2 poll < res=1 fds=12:44 
1631268063206947003 apache2 getsockopt >
1631268063206948092 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268063206948714 apache2 fcntl > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063206948971 apache2 fcntl < res=0(<f>/dev/null) 
1631268063206949424 mysqld poll < res=1 fds=20:41 
1631268063206950587 apache2 setsockopt >
1631268063206951393 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063206951815 apache2 setsockopt >
1631268063206952596 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268063206952679 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063206952932 mysqld fcntl < res=2(<p>pipe:[368810612]) 
1631268063206953133 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063206953325 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206954075 mysqld accept >
1631268063206954481 apache2 poll > fds=12:431 timeout=1471228928 
1631268063206960349 mysqld accept < fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) tuple=127.0.0.1:60508->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268063206960991 mysqld fcntl > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268063206961140 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206961264 mysqld fcntl > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063206961396 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206962153 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063206962268 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206962381 mysqld fcntl > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063206962468 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206978009 mysqld fcntl > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063206978195 mysqld fcntl < res=0(<f>/dev/null) 
1631268063206978438 mysqld setsockopt >
1631268063206979589 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268063206979996 mysqld setsockopt >
1631268063206980284 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063206981333 mysqld futex > addr=55C85FAC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268063206984251 mysqld futex < res=1 
1631268063206984905 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268063206987876 mysqld futex < res=0 
1631268063206989804 mysqld futex > addr=55C85FABEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268063206990309 mysqld futex < res=0 
1631268063206991328 mysqld gettid >
1631268063206991960 mysqld gettid <
1631268063206996015 mysqld getpeername >
1631268063206997386 mysqld getpeername <
1631268063207005225 mysqld setsockopt >
1631268063207006304 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063207011515 mysqld sendto > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=102 tuple=NULL 
1631268063207027709 apache2 poll < res=1 fds=12:41 
1631268063207028314 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207029387 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268063207031471 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEArQAAACU3J1hqKzRiAP/3LQIAP6AVAAAAAAAAAAAAAHE0S154YFZuSFprLQA= 
1631268063207033125 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207033980 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063207034161 apache2 poll > fds=12:431 timeout=1471228928 
1631268063207034730 apache2 poll < res=1 fds=12:41 
1631268063207034947 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=102 
1631268063207035053 mysqld poll > fds=41:43 timeout=10000 
1631268063207035842 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQCtAAAAJTcnWGorNGIA//ctAgA/oBUAAAAAAAAAAAAAcTRLXnhgVm5IWmstAG15c3E= tuple=NULL 
1631268063207042020 apache2 sendto > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=106 tuple=NULL 
1631268063207055546 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABQ9ixj+teTM5w5jCcE49J2cwXgUggBteXNxbF9uYXRpdmVfcGFzc3c= 
1631268063207055636 mysqld poll < res=1 fds=41:41 
1631268063207056603 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207057079 apache2 poll > fds=12:431 timeout=1471228928 
1631268063207057834 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631268063207058433 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=102 
1631268063207059406 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFD2LGP615MznDmMJwTj0nZzBeBSCAG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631268063207065143 mysqld sendto > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=48 tuple=NULL 
1631268063207076905 apache2 poll < res=1 fds=12:41 
1631268063207077384 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207077672 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQAJTcnWGorNGJxNEteeGBWbkhaay0A 
1631268063207078194 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631268063207078547 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207079056 apache2 poll > fds=12:431 timeout=1471228928 
1631268063207079078 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063207079509 mysqld poll > fds=41:43 timeout=10000 
1631268063207079516 apache2 poll < res=1 fds=12:41 
1631268063207079742 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=102 
1631268063207080449 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZAAlNydYais0YnE0S154YFZuSFprLQA= tuple=NULL 
1631268063207084091 apache2 sendto > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=24 tuple=NULL 
1631268063207094497 apache2 sendto < res=24 data=FAAAAz2LGP615MznDmMJwTj0nZzBeBSC 
1631268063207094744 mysqld poll < res=1 fds=41:41 
1631268063207095405 apache2 poll > fds=12:431 timeout=1471228928 
1631268063207095423 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207096260 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631268063207096717 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=20 
1631268063207097569 mysqld recvfrom < res=20 data=PYsY/rXkzOcOYwnBOPSdnMF4FII= tuple=NULL 
1631268063207103067 mysqld sendto > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=11 tuple=NULL 
1631268063207113232 apache2 poll < res=1 fds=12:41 
1631268063207113641 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631268063207113688 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=58 
1631268063207114880 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631268063207117378 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207117996 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063207118484 mysqld poll > fds=41:43 timeout=28800000 
1631268063207132457 apache2 sendto > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=13 tuple=NULL 
1631268063207142072 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631268063207143086 mysqld poll < res=1 fds=41:41 
1631268063207143514 apache2 poll > fds=12:431 timeout=1471228928 
1631268063207144007 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207144918 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631268063207145639 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=9 
1631268063207146485 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631268063207162912 mysqld access > mode=0(F_OK) 
1631268063207171530 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268063207178059 mysqld sendto > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=11 tuple=NULL 
1631268063207191035 apache2 poll < res=1 fds=12:41 
1631268063207191588 apache2 recvfrom > fd=12(<4t>127.0.0.1:60508->127.0.0.1:3306) size=47 
1631268063207191644 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631268063207192933 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631268063207195230 mysqld recvfrom > fd=41(<4t>127.0.0.1:60508->127.0.0.1:3306) size=4 
1631268063207196055 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268063207196601 mysqld poll > fds=41:43 timeout=28800000 
1631268063207221406 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268063207225781 apache2 socket < fd=13(<4>) 
1631268063207226123 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631268063207226467 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268063207226652 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631268063207226845 apache2 fcntl < res=0(<f>/dev/null) 
1631268063207227100 apache2 connect > fd=13(<4>) 
1631268063207253179 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:60510->127.0.0.1:3306 
1631268063207254094 apache2 poll > fds=13:435 timeout=60000 
1631268063207254899 apache2 poll < res=1 fds=13:44 
1631268063207255215 apache2 getsockopt >
1631268063207255576 mysqld poll < res=1 fds=20:41 
1631268063207255914 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268063207256467 apache2 fcntl > fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063207256731 apache2 fcntl < res=0(<f>/dev/null) 
1631268063207256805 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268063207257103 mysqld fcntl < res=2(<p>pipe:[368810612]) 
1631268063207257273 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063207257477 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207257694 mysqld accept >
1631268063207258098 apache2 setsockopt >
1631268063207258689 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063207259072 apache2 setsockopt >
1631268063207259571 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063207260352 apache2 poll > fds=13:431 timeout=1471228928 
1631268063207263444 mysqld accept < fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) tuple=127.0.0.1:60510->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268063207264078 mysqld fcntl > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268063207264252 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207264367 mysqld fcntl > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063207264516 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207264766 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063207264879 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207264996 mysqld fcntl > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268063207265087 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207276338 mysqld fcntl > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268063207276548 mysqld fcntl < res=0(<f>/dev/null) 
1631268063207276842 mysqld setsockopt >
1631268063207277707 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268063207278114 mysqld setsockopt >
1631268063207278384 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268063207278941 mysqld futex > addr=55C85FAC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268063207281802 mysqld futex < res=1 
1631268063207282172 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268063207285333 mysqld futex < res=0 
1631268063207286585 mysqld futex > addr=55C85FABEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268063207286921 mysqld futex < res=0 
1631268063207287439 mysqld gettid >
1631268063207287962 mysqld gettid <
1631268063207290016 mysqld getpeername >
1631268063207291546 mysqld getpeername <
1631268063207295584 mysqld setsockopt >
1631268063207296501 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268063207299208 mysqld sendto > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) size=102 tuple=NULL 
1631268063207313430 apache2 poll < res=1 fds=13:41 
1631268063207313871 apache2 recvfrom > fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) size=4 
1631268063207314856 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268063207316010 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEArgAAADQxN19ZI0FbAP/3LQIAP6AVAAAAAAAAAAAAACpaaSJoaVRITi8/MAA= 
1631268063207316016 apache2 poll > fds=13:431 timeout=1471228928 
1631268063207316482 apache2 poll < res=1 fds=13:41 
1631268063207316671 apache2 recvfrom > fd=13(<4t>127.0.0.1:60510->127.0.0.1:3306) size=102 
1631268063207316973 mysqld recvfrom > fd=74(<4t>127.0.0.1:60510->127.0.0.1:3306) size=4 
