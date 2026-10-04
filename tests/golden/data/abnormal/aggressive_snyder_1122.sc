1631268162003438805 apache2 getsockname >
1631268162003439649 apache2 getsockname <
1631268162003446715 apache2 fcntl > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) cmd=4(F_GETFL) 
1631268162003447045 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162003447182 apache2 fcntl > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) cmd=5(F_SETFL) 
1631268162003447407 apache2 fcntl < res=0(<f>/dev/null) 
1631268162003470541 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162003472824 apache2 mmap < res=7F6CF08FC000 vm_size=374020 vm_rss=9104 vm_swap=0 
1631268162003483755 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162003484411 apache2 mmap < res=7F6CF08FA000 vm_size=374028 vm_rss=9104 vm_swap=0 
1631268162003486171 apache2 read > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=8000 
1631268162003488975 apache2 read < res=434 data=R0VUIC9sb2dpbi5waHAgSFRUUC8xLjENCkhvc3Q6IDAzMTVmZDIyMDAwYzRiZmINCkNvbm5lY3Rpb246IGtlZXAtYWxpdmUNClVwZ3JhZGU= 
1631268162003533989 apache2 stat >
1631268162003541652 apache2 stat < res=0 path=/var/www/html/login.php 
1631268162003556045 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162003557091 apache2 mmap < res=7F6CF08F8000 vm_size=374036 vm_rss=9104 vm_swap=0 
1631268162003643275 apache2 brk > addr=563D8EAE4000 
1631268162003645462 apache2 brk < res=563D8EAE4000 vm_size=374224 vm_rss=9104 vm_swap=0 
1631268162003783386 apache2 brk > addr=563D8EB05000 
1631268162003784269 apache2 brk < res=563D8EB05000 vm_size=374356 vm_rss=11012 vm_swap=0 
1631268162003814013 apache2 setitimer >
1631268162003815446 apache2 setitimer <
1631268162003815810 apache2 rt_sigaction >
1631268162003816185 apache2 rt_sigaction <
1631268162003816603 apache2 rt_sigprocmask >
1631268162003816769 apache2 rt_sigprocmask <
1631268162003867806 apache2 mmap > addr=0 length=65536 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162003868853 apache2 mmap < res=7F6CF08E8000 vm_size=374420 vm_rss=11316 vm_swap=0 
1631268162003894508 apache2 getcwd >
1631268162003895523 apache2 getcwd < res=2 path=/ 
1631268162003896385 apache2 chdir >
1631268162003899351 apache2 chdir < res=0 path=/var/www/html 
1631268162003901564 apache2 setitimer >
1631268162003901840 apache2 setitimer <
1631268162003907417 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162003910078 apache2 fcntl < res=0(<f>/dev/null) 
1631268162003922029 apache2 lstat >
1631268162003924566 apache2 lstat < res=0 path=/var/www/html/login.php 
1631268162003925027 apache2 lstat >
1631268162003926421 apache2 lstat < res=0 path=/var/www/html 
1631268162003926783 apache2 lstat >
1631268162003928072 apache2 lstat < res=0 path=/var/www 
1631268162003928578 apache2 lstat >
1631268162003929718 apache2 lstat < res=0 path=/var 
1631268162003940298 apache2 stat >
1631268162003941691 apache2 stat < res=0 path=/var/www/html/login.php 
1631268162003965114 apache2 getcwd >
1631268162003965573 apache2 getcwd < res=14 path=/var/www/html 
1631268162003976900 apache2 stat >
1631268162003980132 apache2 stat < res=0 path=/var/www/html/dvwa/includes/dvwaPage.inc.php 
1631268162004023896 apache2 getpid >
1631268162004024457 apache2 getpid <
1631268162004032059 apache2 open >
1631268162004038343 apache2 open < fd=11(<f>/dev/urandom) name=/dev/urandom flags=1(O_RDONLY) mode=0 dev=200018 
1631268162004041709 apache2 read > fd=11(<f>/dev/urandom) size=32 
1631268162004042711 apache2 read < res=32 data=BoU+aVqtFW8YsbA96l9mfeRKsToDAQAlZ5l8h+ejZu4= 
1631268162004043347 apache2 close > fd=11(<f>/dev/urandom) 
1631268162004043638 apache2 close < res=0 
1631268162004046491 apache2 stat >
1631268162004059318 apache2 stat < res=-2(ENOENT) path=/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5 
1631268162004068993 apache2 open >
1631268162004086744 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) name=/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5 flags=7(O_CREAT|O_RDWR) mode=0600 dev=200014 
1631268162004087849 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) 
1631268162004088663 apache2 fstat < res=0 
1631268162004088928 apache2 getuid >
1631268162004089206 apache2 getuid < uid=33(www-data) 
1631268162004089524 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) operation=2(LOCK_EX) 
1631268162004091393 apache2 flock < res=0 
1631268162004091626 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) cmd=3(F_SETFD) 
1631268162004091889 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004092043 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) 
1631268162004092531 apache2 fstat < res=0 
1631268162004099240 apache2 access > mode=0(F_OK) 
1631268162004102253 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268162004103903 apache2 stat >
1631268162004105660 apache2 stat < res=0 path=/var/www/html/config/config.inc.php 
1631268162004111939 apache2 stat >
1631268162004114222 apache2 stat < res=0 path=/var/www/html/dvwa/includes/dvwaPhpIds.inc.php 
1631268162004127345 apache2 stat >
1631268162004131442 apache2 stat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/Init.php 
1631268162004155899 apache2 getcwd >
1631268162004156378 apache2 getcwd < res=14 path=/var/www/html 
1631268162004157531 apache2 lstat >
1631268162004160328 apache2 lstat < res=0 path=/var/www/html/hackable/uploads 
1631268162004160835 apache2 lstat >
1631268162004162183 apache2 lstat < res=0 path=/var/www/html/hackable 
1631268162004163361 apache2 getcwd >
1631268162004163605 apache2 getcwd < res=14 path=/var/www/html 
1631268162004164487 apache2 lstat >
1631268162004167338 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268162004167953 apache2 lstat >
1631268162004169499 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp 
1631268162004170044 apache2 lstat >
1631268162004171946 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS 
1631268162004172455 apache2 lstat >
1631268162004174042 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib 
1631268162004174496 apache2 lstat >
1631268162004175811 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6 
1631268162004176245 apache2 lstat >
1631268162004177484 apache2 lstat < res=0 path=/var/www/html/external/phpids 
1631268162004177904 apache2 lstat >
1631268162004179010 apache2 lstat < res=0 path=/var/www/html/external 
1631268162004180587 apache2 getcwd >
1631268162004180817 apache2 getcwd < res=14 path=/var/www/html 
1631268162004181281 apache2 lstat >
1631268162004182739 apache2 lstat < res=0 path=/var/www/html/config 
1631268162004194462 apache2 open >
1631268162004198965 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162004200331 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631268162004200697 apache2 lseek < res=0 
1631268162004201360 apache2 fstat > fd=12(<f>/etc/passwd) 
1631268162004201946 apache2 fstat < res=0 
1631268162004202100 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631268162004204222 apache2 mmap < res=7F6CF0A4B000 vm_size=374424 vm_rss=12956 vm_swap=0 
1631268162004204416 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631268162004204843 apache2 lseek < res=1022 
1631268162004208889 apache2 munmap > addr=7F6CF0A4B000 length=1022 
1631268162004211369 apache2 munmap < res=0 vm_size=374420 vm_rss=13840 vm_swap=0 
1631268162004211562 apache2 close > fd=12(<f>/etc/passwd) 
1631268162004211821 apache2 close < res=0 
1631268162004215130 apache2 access > mode=2(W_OK) 
1631268162004217693 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631268162004218723 apache2 access > mode=2(W_OK) 
1631268162004219915 apache2 access < res=0 name=/var/www/html/config 
1631268162004220534 apache2 access > mode=2(W_OK) 
1631268162004222246 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268162004256553 apache2 socket > domain=10(AF_INET6) type=2 proto=0 
1631268162004260428 apache2 socket < fd=12(<6>) 
1631268162004262363 apache2 close > fd=12(<6>) 
1631268162004262574 apache2 close < res=0 
1631268162004267536 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268162004270486 apache2 socket < fd=12(<4>) 
1631268162004270783 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631268162004271051 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162004271171 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631268162004271338 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004271458 apache2 connect > fd=12(<4>) 
1631268162004302700 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:35126->127.0.0.1:3306 
1631268162004303843 apache2 poll > fds=12:435 timeout=60000 
1631268162004304737 apache2 poll < res=1 fds=12:44 
1631268162004305020 apache2 getsockopt >
1631268162004305561 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268162004306024 apache2 fcntl > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004306225 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004307502 mysqld poll < res=1 fds=20:41 
1631268162004307511 apache2 setsockopt >
1631268162004308011 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162004308397 apache2 setsockopt >
1631268162004308990 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162004309725 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268162004310043 mysqld fcntl < res=2(<p>pipe:[368952495]) 
1631268162004310263 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004310334 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004310416 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004310774 mysqld accept >
1631268162004316790 mysqld accept < fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) tuple=127.0.0.1:35126->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268162004317436 mysqld fcntl > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268162004317571 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004317688 mysqld fcntl > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162004317822 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004318306 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004318423 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004318547 mysqld fcntl > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162004318643 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004334097 mysqld fcntl > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004334284 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004334518 mysqld setsockopt >
1631268162004335454 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268162004335857 mysqld setsockopt >
1631268162004336151 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162004337215 mysqld futex > addr=562726CC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268162004340577 mysqld futex < res=1 
1631268162004341261 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268162004344102 mysqld futex < res=0 
1631268162004345746 mysqld futex > addr=562726CBEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268162004346178 mysqld futex < res=0 
1631268162004346843 mysqld gettid >
1631268162004347224 mysqld gettid <
1631268162004350283 mysqld getpeername >
1631268162004351444 mysqld getpeername <
1631268162004357467 mysqld setsockopt >
1631268162004358331 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162004362055 mysqld sendto > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=102 tuple=NULL 
1631268162004375421 apache2 poll < res=1 fds=12:41 
1631268162004376196 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004377412 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268162004377957 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAuwAAADR6LnN5Kl58AP/3LQIAP6AVAAAAAAAAAAAAAHZcSj42NEAnQVNcVgA= 
1631268162004379434 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004380139 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004381081 mysqld poll > fds=41:43 timeout=10000 
1631268162004382150 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004382759 apache2 poll < res=1 fds=12:41 
1631268162004383046 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=102 
1631268162004384188 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC7AAAANHouc3kqXnwA//ctAgA/oBUAAAAAAAAAAAAAdlxKPjY0QCdBU1xWAG15c3E= tuple=NULL 
1631268162004390988 apache2 sendto > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=106 tuple=NULL 
1631268162004403587 mysqld poll < res=1 fds=41:41 
1631268162004403925 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABT5tOYppzeGsR1fCub64CIIQVxpsABteXNxbF9uYXRpdmVfcGFzc3c= 
1631268162004404589 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004405297 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004405656 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631268162004406247 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=102 
1631268162004407159 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFPm05imnN4axHV8K5vrgIghBXGmwAG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631268162004412411 mysqld sendto > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=48 tuple=NULL 
1631268162004421573 apache2 poll < res=1 fds=12:41 
1631268162004422092 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQANHouc3kqXnx2XEo+NjRAJ0FTXFYA 
1631268162004422203 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004422895 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004423102 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631268162004423340 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004423772 mysqld poll > fds=41:43 timeout=10000 
1631268162004424184 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004424664 apache2 poll < res=1 fds=12:41 
1631268162004424945 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=102 
1631268162004425760 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZAA0ei5zeSpefHZcSj42NEAnQVNcVgA= tuple=NULL 
1631268162004431810 apache2 sendto > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=24 tuple=NULL 
1631268162004441294 mysqld poll < res=1 fds=41:41 
1631268162004441361 apache2 sendto < res=24 data=FAAAA/m05imnN4axHV8K5vrgIghBXGmw 
1631268162004442074 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004442307 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004442922 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631268162004443438 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=20 
1631268162004444128 mysqld recvfrom < res=20 data=+bTmKac3hrEdXwrm+uAiCEFcabA= tuple=NULL 
1631268162004449038 mysqld sendto > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=11 tuple=NULL 
1631268162004457595 apache2 poll < res=1 fds=12:41 
1631268162004457641 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631268162004458188 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=58 
1631268162004459147 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631268162004461076 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004461746 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004462164 mysqld poll > fds=41:43 timeout=28800000 
1631268162004475921 apache2 sendto > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=13 tuple=NULL 
1631268162004485936 mysqld poll < res=1 fds=41:41 
1631268162004486103 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631268162004486761 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004487629 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631268162004487805 apache2 poll > fds=12:431 timeout=1471228928 
1631268162004488364 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=9 
1631268162004489052 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631268162004500740 mysqld access > mode=0(F_OK) 
1631268162004506726 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268162004511605 mysqld sendto > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=11 tuple=NULL 
1631268162004521712 apache2 poll < res=1 fds=12:41 
1631268162004521719 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631268162004522305 apache2 recvfrom > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=47 
1631268162004523442 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631268162004525038 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004525579 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004526014 mysqld poll > fds=41:43 timeout=28800000 
1631268162004545425 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268162004549193 apache2 socket < fd=13(<4>) 
1631268162004549496 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631268162004549774 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162004549893 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631268162004550002 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004550121 apache2 connect > fd=13(<4>) 
1631268162004570653 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:35128->127.0.0.1:3306 
1631268162004571450 apache2 poll > fds=13:435 timeout=60000 
1631268162004572147 apache2 poll < res=1 fds=13:44 
1631268162004572378 apache2 getsockopt >
1631268162004572512 mysqld poll < res=1 fds=20:41 
1631268162004572903 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268162004573327 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268162004573360 apache2 fcntl > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004573546 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004573613 mysqld fcntl < res=2(<p>pipe:[368952495]) 
1631268162004573780 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004573925 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004574141 mysqld accept >
1631268162004574434 apache2 setsockopt >
1631268162004574858 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162004575136 apache2 setsockopt >
1631268162004575526 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162004576155 apache2 poll > fds=13:431 timeout=1471228928 
1631268162004577933 mysqld accept < fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) tuple=127.0.0.1:35128->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268162004578452 mysqld fcntl > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268162004578581 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004578700 mysqld fcntl > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162004578830 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004579013 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004579114 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004579233 mysqld fcntl > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162004579328 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004584711 mysqld fcntl > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162004584872 mysqld fcntl < res=0(<f>/dev/null) 
1631268162004585075 mysqld setsockopt >
1631268162004585675 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268162004585976 mysqld setsockopt >
1631268162004586257 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162004586694 mysqld futex > addr=562726CC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268162004589470 mysqld futex < res=1 
1631268162004589724 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268162004592403 mysqld futex < res=0 
1631268162004593724 mysqld futex > addr=562726CBEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268162004594045 mysqld futex < res=0 
1631268162004594816 mysqld gettid >
1631268162004595181 mysqld gettid <
1631268162004597225 mysqld getpeername >
1631268162004598470 mysqld getpeername <
1631268162004602086 mysqld setsockopt >
1631268162004603164 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162004606014 mysqld sendto > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=102 tuple=NULL 
1631268162004621230 apache2 poll < res=1 fds=13:41 
1631268162004621689 apache2 recvfrom > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004622585 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268162004623592 apache2 poll > fds=13:431 timeout=1471228928 
1631268162004623955 apache2 poll < res=1 fds=13:41 
1631268162004624127 apache2 recvfrom > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=102 
1631268162004624294 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAvAAAAC5iJjJmMFtYAP/3LQIAP6AVAAAAAAAAAAAAAClfKEVkR3Y9bS48IwA= 
1631268162004624826 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC8AAAALmImMmYwW1gA//ctAgA/oBUAAAAAAAAAAAAAKV8oRWRHdj1tLjwjAG15c3E= tuple=NULL 
1631268162004625364 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004626038 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004626697 mysqld poll > fds=74:43 timeout=10000 
1631268162004628637 apache2 sendto > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=110 tuple=NULL 
1631268162004638231 apache2 sendto < res=110 data=agAAAY2iCwAAAADAIQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABRAo2qkX2ySoS5GI2NFXWAUJIKOXWR2d2EAbXlzcWxfbmF0aXZlX3A= 
1631268162004639097 apache2 poll > fds=13:431 timeout=1471228928 
1631268162004689300 mysqld poll < res=1 fds=74:41 
1631268162004690698 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004692093 mysqld recvfrom < res=4 data=agAAAQ== tuple=NULL 
1631268162004692666 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=106 
1631268162004693658 mysqld recvfrom < res=106 data=jaILAAAAAMAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFECjaqRfbJKhLkYjY0VdYBQkgo5dZHZ3YQBteXNxbF9uYXRpdmVfcGFzc3c= tuple=NULL 
1631268162004700231 mysqld access > mode=0(F_OK) 
1631268162004704916 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268162004706868 mysqld sendto > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=11 tuple=NULL 
1631268162004719281 apache2 poll < res=1 fds=13:41 
1631268162004719574 apache2 recvfrom > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004720290 apache2 recvfrom < res=4 data=BwAAAg== tuple=NULL 
1631268162004720408 mysqld sendto < res=11 data=BwAAAgAAAAIAAAA= 
1631268162004720836 apache2 poll > fds=13:431 timeout=1471228928 
1631268162004721140 apache2 poll < res=1 fds=13:41 
1631268162004721313 apache2 recvfrom > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=102 
1631268162004721867 apache2 recvfrom < res=7 data=AAAAAgAAAA== tuple=NULL 
1631268162004722906 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004723422 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162004723923 mysqld poll > fds=74:43 timeout=28800000 
1631268162004735765 apache2 nanosleep > interval=0(0s) 
1631268162004789876 apache2 nanosleep < res=0 
1631268162004806960 apache2 chdir >
1631268162004808754 apache2 chdir < res=0 path=/ 
1631268162004812650 apache2 sendto > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) size=5 tuple=NULL 
1631268162004822094 apache2 sendto < res=5 data=AQAAAAE= 
1631268162004823153 mysqld poll < res=1 fds=41:41 
1631268162004824007 apache2 close > fd=12(<4t>127.0.0.1:35126->127.0.0.1:3306) 
1631268162004824032 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=4 
1631268162004824434 apache2 close < res=0 
1631268162004825122 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268162004825867 mysqld recvfrom > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) size=1 
1631268162004826648 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268162004829753 mysqld shutdown > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268162004839069 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162004841324 apache2 mmap < res=7F6CF08E6000 vm_size=374428 vm_rss=13840 vm_swap=0 
1631268162004844837 mysqld shutdown < res=0 
1631268162004845433 mysqld close > fd=41(<4t>127.0.0.1:35126->127.0.0.1:3306) 
1631268162004845811 mysqld close < res=0 
1631268162004848352 apache2 setitimer >
1631268162004848898 apache2 setitimer <
1631268162004857845 mysqld futex > addr=562726CC1364 op=128(FUTEX_PRIVATE_FLAG) val=367 
1631268162004871528 apache2 pwrite > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) size=65 pos=0 
1631268162004883567 apache2 pwrite < res=65 data=ZHZ3YXxhOjA6e31zZXNzaW9uX3Rva2VufHM6MzI6ImU5OThjMWZhYTU0OTdhZGJkNDQ0NjYyNGRhMzljY2UwIjs= 
1631268162004884281 apache2 close > fd=11(<f>/var/lib/php/sessions/sess_gthu9nvubgpkfc4uuccs6ufer5) 
1631268162004884594 apache2 close < res=0 
1631268162004890794 apache2 sendto > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) size=5 tuple=NULL 
1631268162004901883 apache2 sendto < res=5 data=AQAAAAE= 
1631268162004902828 apache2 close > fd=13(<4t>127.0.0.1:35128->127.0.0.1:3306) 
1631268162004903082 apache2 close < res=0 
1631268162004917173 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162004918643 apache2 fcntl < res=0(<f>/dev/null) 
1631268162004923744 apache2 setitimer >
1631268162004924024 apache2 setitimer <
1631268162004930283 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162004931942 apache2 mmap < res=7F6CF08E4000 vm_size=374436 vm_rss=13840 vm_swap=0 
1631268162004941917 apache2 brk > addr=563D8EB2A000 
1631268162004942957 apache2 brk < res=563D8EB2A000 vm_size=374584 vm_rss=13840 vm_swap=0 
1631268162004946076 apache2 mmap > addr=0 length=135168 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162004946418 mysqld poll < res=1 fds=74:41 
1631268162004946648 apache2 mmap < res=7F6CF08C3000 vm_size=374716 vm_rss=13840 vm_swap=0 
1631268162004947813 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=4 
1631268162004949176 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268162004949873 mysqld recvfrom > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) size=1 
1631268162004950767 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268162004953989 mysqld shutdown > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268162004969187 mysqld shutdown < res=0 
1631268162004969591 mysqld close > fd=74(<4t>127.0.0.1:35128->127.0.0.1:3306) 
1631268162004969995 mysqld close < res=0 
1631268162004981178 mysqld futex > addr=562726CC1364 op=128(FUTEX_PRIVATE_FLAG) val=368 
1631268162005030078 apache2 munmap > addr=7F6CF08C3000 length=135168 
1631268162005036080 apache2 munmap < res=0 vm_size=374584 vm_rss=14804 vm_swap=0 
1631268162005036629 apache2 brk > addr=563D8EB08000 
1631268162005043901 apache2 brk < res=563D8EB08000 vm_size=374448 vm_rss=14672 vm_swap=0 
1631268162005049974 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162005050935 apache2 mmap < res=7F6CF08E2000 vm_size=374456 vm_rss=14672 vm_swap=0 
1631268162005059655 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162005060141 apache2 mmap < res=7F6CF08E0000 vm_size=374464 vm_rss=14672 vm_swap=0 
1631268162005064771 apache2 read > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=8000 
1631268162005066065 apache2 read < res=-11(EAGAIN) data= 
1631268162005069015 apache2 writev > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=1191 
1631268162005093703 apache2 writev < res=1191 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268162005107577 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=194 
1631268162005114420 apache2 write < res=194 data=MTkyLjE2OC42NC4xOCAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9sb2dpbi5waHAgSFRUUC8xLjEiIDIwMCAxMTk= 
1631268162005115226 apache2 times >
1631268162005116244 apache2 times <
1631268162005122593 apache2 poll > fds=10:41 timeout=5000 
1631268162007759005 mysqld io_getevents <
1631268162007761305 mysqld io_getevents >
1631268162016837428 apache2 poll < res=1 fds=10:41 
1631268162016840631 apache2 read > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=8000 
1631268162016843320 apache2 read < res=400 data=R0VUIC9kdndhL2Nzcy9sb2dpbi5jc3MgSFRUUC8xLjENCkhvc3Q6IDAzMTVmZDIyMDAwYzRiZmINCkNvbm5lY3Rpb246IGtlZXAtYWxpdmU= 
1631268162016888338 apache2 stat >
1631268162016899833 apache2 stat < res=0 path=/var/www/html/dvwa/css/login.css 
1631268162016927568 apache2 open >
1631268162016938307 apache2 open < fd=11(<f>/var/www/html/dvwa/css/login.css) name=/var/www/html/dvwa/css/login.css flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162016950187 apache2 mmap > addr=0 length=842 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/css/login.css) offset=0 
1631268162016954678 apache2 mmap < res=7F6CF0A4B000 vm_size=374468 vm_rss=14672 vm_swap=0 
1631268162016960573 apache2 brk > addr=563D8EB2A000 
1631268162016963022 apache2 brk < res=563D8EB2A000 vm_size=374604 vm_rss=14672 vm_swap=0 
1631268162016967199 apache2 brk > addr=563D8EB6A000 
1631268162016967888 apache2 brk < res=563D8EB6A000 vm_size=374860 vm_rss=14672 vm_swap=0 
1631268162017028856 apache2 accept < fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) tuple=192.168.64.18:36164->192.168.64.19:80 queuepct=0 queuelen=0 queuemax=511 
1631268162017031750 apache2 munmap > addr=7F6CF0A4B000 length=842 
1631268162017035352 apache2 munmap < res=0 vm_size=374856 vm_rss=14892 vm_swap=0 
1631268162017046356 apache2 getsockname >
1631268162017047576 apache2 getsockname <
1631268162017055888 apache2 fcntl > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) cmd=4(F_GETFL) 
1631268162017056197 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162017056356 apache2 fcntl > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) cmd=5(F_SETFL) 
1631268162017056512 apache2 fcntl < res=0(<f>/dev/null) 
1631268162017061838 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162017061958 apache2 brk > addr=563D8EB2A000 
1631268162017064952 apache2 mmap < res=7F6CF08FC000 vm_size=374020 vm_rss=9104 vm_swap=0 
1631268162017067664 apache2 brk < res=563D8EB2A000 vm_size=374600 vm_rss=14880 vm_swap=0 
1631268162017068153 apache2 brk > addr=563D8EB08000 
1631268162017075252 apache2 brk < res=563D8EB08000 vm_size=374464 vm_rss=14748 vm_swap=0 
1631268162017076350 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162017077583 apache2 mmap < res=7F6CF08FA000 vm_size=374028 vm_rss=9104 vm_swap=0 
1631268162017079545 apache2 read > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=8000 
1631268162017082648 apache2 read < res=454 data=R0VUIC9kdndhL2ltYWdlcy9sb2dpbl9sb2dvLnBuZyBIVFRQLzEuMQ0KSG9zdDogMDMxNWZkMjIwMDBjNGJmYg0KQ29ubmVjdGlvbjoga2U= 
1631268162017086073 apache2 read > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=8000 
1631268162017087230 apache2 read < res=-11(EAGAIN) data= 
1631268162017088918 apache2 writev > fd=10(<4t>192.168.64.18:36162->192.168.64.19:80) size=741 
1631268162017110499 apache2 writev < res=741 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268162017116576 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=234 
1631268162017124695 apache2 write < res=234 data=MTkyLjE2OC42NC4xOCAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9kdndhL2Nzcy9sb2dpbi5jc3MgSFRUUC8xLjE= 
1631268162017125807 apache2 times >
1631268162017127220 apache2 times <
1631268162017127649 apache2 close > fd=11(<f>/var/www/html/dvwa/css/login.css) 
1631268162017128053 apache2 close < res=0 
1631268162017132173 apache2 stat >
1631268162017132985 apache2 poll > fds=10:41 timeout=5000 
1631268162017139765 apache2 stat < res=0 path=/var/www/html/dvwa/images/login_logo.png 
1631268162017149580 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162017151413 apache2 mmap < res=7F6CF08F8000 vm_size=374036 vm_rss=9104 vm_swap=0 
1631268162017197360 apache2 open >
1631268162017205890 apache2 open < fd=11(<f>/var/www/html/dvwa/images/login_logo.png) name=/var/www/html/dvwa/images/login_logo.png flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162017218193 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162017219809 apache2 mmap < res=7F6CF08F6000 vm_size=374044 vm_rss=9104 vm_swap=0 
1631268162017228176 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631268162017229083 apache2 mmap < res=7F6CF08F4000 vm_size=374052 vm_rss=9104 vm_swap=0 
1631268162017231722 apache2 mmap > addr=0 length=9088 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/images/login_logo.png) offset=0 
1631268162017233782 apache2 mmap < res=7F6CF08F1000 vm_size=374064 vm_rss=9104 vm_swap=0 
1631268162017236197 apache2 writev > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=9375 
1631268162017301624 apache2 writev < res=9375 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268162017305663 apache2 munmap > addr=7F6CF08F1000 length=9088 
1631268162017310063 apache2 munmap < res=0 vm_size=374052 vm_rss=10276 vm_swap=0 
1631268162017328004 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=243 
1631268162017334651 apache2 write < res=243 data=MTkyLjE2OC42NC4xOCAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9kdndhL2ltYWdlcy9sb2dpbl9sb2dvLnBuZyA= 
1631268162017335568 apache2 times >
1631268162017336608 apache2 times <
1631268162017337081 apache2 close > fd=11(<f>/var/www/html/dvwa/images/login_logo.png) 
1631268162017337303 apache2 close < res=0 
1631268162017341978 apache2 read > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=8000 
1631268162017343204 apache2 read < res=-11(EAGAIN) data= 
1631268162017350737 apache2 poll > fds=10:41 timeout=5000 
1631268162035237552 apache2 poll < res=1 fds=10:41 
1631268162035239988 apache2 read > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=8000 
1631268162035243003 apache2 read < res=439 data=R0VUIC9mYXZpY29uLmljbyBIVFRQLzEuMQ0KSG9zdDogMDMxNWZkMjIwMDBjNGJmYg0KQ29ubmVjdGlvbjoga2VlcC1hbGl2ZQ0KVXNlci0= 
1631268162035288548 apache2 stat >
1631268162035296555 apache2 stat < res=0 path=/var/www/html/favicon.ico 
1631268162035315828 apache2 open >
1631268162035323090 apache2 open < fd=11(<f>/var/www/html/favicon.ico) name=/var/www/html/favicon.ico flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162035340541 apache2 read > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=8000 
1631268162035341875 apache2 read < res=-11(EAGAIN) data= 
1631268162035343276 apache2 mmap > addr=0 length=1406 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/favicon.ico) offset=0 
1631268162035347246 apache2 mmap < res=7F6CF0A4B000 vm_size=374056 vm_rss=10276 vm_swap=0 
1631268162035348152 apache2 writev > fd=10(<4t>192.168.64.18:36164->192.168.64.19:80) size=1706 
1631268162035381359 apache2 writev < res=1706 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268162035383123 apache2 munmap > addr=7F6CF0A4B000 length=1406 
1631268162035387151 apache2 munmap < res=0 vm_size=374052 vm_rss=10340 vm_swap=0 
1631268162035392042 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=228 
1631268162035402000 apache2 write < res=228 data=MTkyLjE2OC42NC4xOCAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9mYXZpY29uLmljbyBIVFRQLzEuMSIgMjAwIDE= 
1631268162035403118 apache2 times >
1631268162035413494 apache2 times <
1631268162035419173 apache2 close > fd=11(<f>/var/www/html/favicon.ico) 
1631268162035419664 apache2 close < res=0 
1631268162035424247 apache2 poll > fds=10:41 timeout=5000 
1631268162065815082 mysqld io_getevents <
1631268162065817740 mysqld io_getevents >
1631268162065918090 mysqld io_getevents <
1631268162065919985 mysqld io_getevents >
1631268162072250192 mysqld io_getevents <
1631268162072251476 mysqld io_getevents >
1631268162104878286 apache2 select < res=0 
1631268162104882194 apache2 wait4 >
1631268162104888191 apache2 wait4 <
1631268162104888833 apache2 select >
1631268162163859067 apache2 poll < res=1 fds=10:41 
1631268162163861863 apache2 read > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=8000 
1631268162163864556 apache2 read < res=546 data=R0VUIC9sb2dvdXQucGhwIEhUVFAvMS4xDQpIb3N0OiAwMzE1ZmQyMjAwMGM0YmZiDQpDb25uZWN0aW9uOiBrZWVwLWFsaXZlDQpVcGdyYWQ= 
1631268162163910878 apache2 stat >
1631268162163921839 apache2 stat < res=0 path=/var/www/html/logout.php 
1631268162163968194 apache2 setitimer >
1631268162163969162 apache2 setitimer <
1631268162163969774 apache2 rt_sigaction >
1631268162163970047 apache2 rt_sigaction <
1631268162163970698 apache2 rt_sigprocmask >
1631268162163970973 apache2 rt_sigprocmask <
1631268162163994148 apache2 getcwd >
1631268162163995077 apache2 getcwd < res=2 path=/ 
1631268162163996040 apache2 chdir >
1631268162163998950 apache2 chdir < res=0 path=/var/www/html 
1631268162164001424 apache2 setitimer >
1631268162164001705 apache2 setitimer <
1631268162164003703 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162164006519 apache2 fcntl < res=0(<f>/dev/null) 
1631268162164009738 apache2 lstat >
1631268162164013452 apache2 lstat < res=0 path=/var/www/html/logout.php 
1631268162164016993 apache2 stat >
1631268162164018809 apache2 stat < res=0 path=/var/www/html/logout.php 
1631268162164025180 apache2 getcwd >
1631268162164025704 apache2 getcwd < res=14 path=/var/www/html 
1631268162164055407 apache2 open >
1631268162164068248 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) name=/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0 flags=7(O_CREAT|O_RDWR) mode=0600 dev=200014 
1631268162164069544 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162164071032 apache2 fstat < res=0 
1631268162164071682 apache2 getuid >
1631268162164072053 apache2 getuid < uid=33(www-data) 
1631268162164072538 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) operation=2(LOCK_EX) 
1631268162164074823 apache2 flock < res=0 
1631268162164075181 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) cmd=3(F_SETFD) 
1631268162164075535 apache2 fcntl < res=0(<f>/dev/null) 
1631268162164075761 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162164076512 apache2 fstat < res=0 
1631268162164076798 apache2 pread > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) size=115 pos=0 
1631268162164085725 apache2 pread < res=115 data=ZHZ3YXxhOjI6e3M6ODoibWVzc2FnZXMiO2E6MDp7fXM6ODoidXNlcm5hbWUiO3M6NzoiZ29yZG9uYiI7fXNlc3Npb25fdG9rZW58czozMjo= 
1631268162164098084 apache2 access > mode=0(F_OK) 
1631268162164104169 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268162164132649 apache2 getcwd >
1631268162164133684 apache2 getcwd < res=14 path=/var/www/html 
1631268162164135947 apache2 getcwd >
1631268162164136248 apache2 getcwd < res=14 path=/var/www/html 
1631268162164137836 apache2 getcwd >
1631268162164138111 apache2 getcwd < res=14 path=/var/www/html 
1631268162164148465 apache2 open >
1631268162164155636 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162164157644 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631268162164158345 apache2 lseek < res=0 
1631268162164159419 apache2 fstat > fd=12(<f>/etc/passwd) 
1631268162164160384 apache2 fstat < res=0 
1631268162164160659 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631268162164166132 apache2 mmap < res=7F6CF0A4B000 vm_size=374672 vm_rss=15740 vm_swap=0 
1631268162164166442 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631268162164166911 apache2 lseek < res=1022 
1631268162164174017 apache2 munmap > addr=7F6CF0A4B000 length=1022 
1631268162164180364 apache2 munmap < res=0 vm_size=374668 vm_rss=15740 vm_swap=0 
1631268162164180683 apache2 close > fd=12(<f>/etc/passwd) 
1631268162164181068 apache2 close < res=0 
1631268162164186457 apache2 access > mode=2(W_OK) 
1631268162164191255 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631268162164192811 apache2 access > mode=2(W_OK) 
1631268162164194869 apache2 access < res=0 name=/var/www/html/config 
1631268162164195923 apache2 access > mode=2(W_OK) 
1631268162164200790 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268162164216365 apache2 pwrite > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) size=117 pos=0 
1631268162164223358 apache2 pwrite < res=117 data=ZHZ3YXxhOjE6e3M6ODoibWVzc2FnZXMiO2E6MTp7aTowO3M6MTk6IllvdSBoYXZlIGxvZ2dlZCBvdXQiO319c2Vzc2lvbl90b2tlbnxzOjM= 
1631268162164224153 apache2 close > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162164224467 apache2 close < res=0 
1631268162164229748 apache2 chdir >
1631268162164231126 apache2 chdir < res=0 path=/ 
1631268162164236120 apache2 setitimer >
1631268162164236577 apache2 setitimer <
1631268162164257160 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162164258811 apache2 fcntl < res=0(<f>/dev/null) 
1631268162164264898 apache2 setitimer >
1631268162164265198 apache2 setitimer <
1631268162164281169 apache2 read > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=8000 
1631268162164283051 apache2 read < res=-11(EAGAIN) data= 
1631268162164285530 apache2 writev > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=336 
1631268162164320002 apache2 writev < res=336 data=SFRUUC8xLjEgMzAyIEZvdW5kDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1ICg= 
1631268162164332953 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=233 
1631268162164339944 apache2 write < res=233 data=MTkyLjE2OC42NC4xMiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9sb2dvdXQucGhwIEhUVFAvMS4xIiAzMDIgMzM= 
1631268162164340999 apache2 times >
1631268162164342431 apache2 times <
1631268162164346582 apache2 poll > fds=10:41 timeout=5000 
1631268162165107248 apache2 poll < res=1 fds=10:41 
1631268162165108923 apache2 read > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=8000 
1631268162165111210 apache2 read < res=545 data=R0VUIC9sb2dpbi5waHAgSFRUUC8xLjENCkhvc3Q6IDAzMTVmZDIyMDAwYzRiZmINCkNvbm5lY3Rpb246IGtlZXAtYWxpdmUNClVwZ3JhZGU= 
1631268162165146563 apache2 stat >
1631268162165154515 apache2 stat < res=0 path=/var/www/html/login.php 
1631268162165194297 apache2 setitimer >
1631268162165195321 apache2 setitimer <
1631268162165195846 apache2 rt_sigaction >
1631268162165196292 apache2 rt_sigaction <
1631268162165196885 apache2 rt_sigprocmask >
1631268162165197470 apache2 rt_sigprocmask <
1631268162165215509 apache2 getcwd >
1631268162165216479 apache2 getcwd < res=2 path=/ 
1631268162165217318 apache2 chdir >
1631268162165219825 apache2 chdir < res=0 path=/var/www/html 
1631268162165221732 apache2 setitimer >
1631268162165222025 apache2 setitimer <
1631268162165223457 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162165226011 apache2 fcntl < res=0(<f>/dev/null) 
1631268162165232577 apache2 getcwd >
1631268162165233133 apache2 getcwd < res=14 path=/var/www/html 
1631268162165258078 apache2 open >
1631268162165270439 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) name=/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0 flags=7(O_CREAT|O_RDWR) mode=0600 dev=200014 
1631268162165271579 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162165272805 apache2 fstat < res=0 
1631268162165273366 apache2 getuid >
1631268162165273650 apache2 getuid < uid=33(www-data) 
1631268162165274085 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) operation=2(LOCK_EX) 
1631268162165276404 apache2 flock < res=0 
1631268162165276821 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) cmd=3(F_SETFD) 
1631268162165277168 apache2 fcntl < res=0(<f>/dev/null) 
1631268162165277471 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162165278255 apache2 fstat < res=0 
1631268162165278563 apache2 pread > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) size=117 pos=0 
1631268162165280743 apache2 pread < res=117 data=ZHZ3YXxhOjE6e3M6ODoibWVzc2FnZXMiO2E6MTp7aTowO3M6MTk6IllvdSBoYXZlIGxvZ2dlZCBvdXQiO319c2Vzc2lvbl90b2tlbnxzOjM= 
1631268162165291570 apache2 access > mode=0(F_OK) 
1631268162165296506 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268162165322182 apache2 getcwd >
1631268162165322991 apache2 getcwd < res=14 path=/var/www/html 
1631268162165326067 apache2 getcwd >
1631268162165326466 apache2 getcwd < res=14 path=/var/www/html 
1631268162165328194 apache2 getcwd >
1631268162165328437 apache2 getcwd < res=14 path=/var/www/html 
1631268162165339203 apache2 open >
1631268162165346046 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=200014 
1631268162165347859 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631268162165348446 apache2 lseek < res=0 
1631268162165349479 apache2 fstat > fd=12(<f>/etc/passwd) 
1631268162165350545 apache2 fstat < res=0 
1631268162165350901 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631268162165356042 apache2 mmap < res=7F6CF0A4B000 vm_size=374672 vm_rss=15740 vm_swap=0 
1631268162165356321 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631268162165356900 apache2 lseek < res=1022 
1631268162165363855 apache2 munmap > addr=7F6CF0A4B000 length=1022 
1631268162165368589 apache2 munmap < res=0 vm_size=374668 vm_rss=15740 vm_swap=0 
1631268162165368855 apache2 close > fd=12(<f>/etc/passwd) 
1631268162165369259 apache2 close < res=0 
1631268162165373909 apache2 access > mode=2(W_OK) 
1631268162165378916 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631268162165380422 apache2 access > mode=2(W_OK) 
1631268162165382484 apache2 access < res=0 name=/var/www/html/config 
1631268162165383618 apache2 access > mode=2(W_OK) 
1631268162165388881 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631268162165420914 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268162165429028 apache2 socket < fd=12(<4>) 
1631268162165429627 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631268162165430021 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162165430198 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631268162165430436 apache2 fcntl < res=0(<f>/dev/null) 
1631268162165430599 apache2 connect > fd=12(<4>) 
1631268162165484079 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:35130->127.0.0.1:3306 
1631268162165485920 apache2 poll > fds=12:435 timeout=60000 
1631268162165487056 apache2 poll < res=1 fds=12:44 
1631268162165487700 apache2 getsockopt >
1631268162165489005 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268162165489916 apache2 fcntl > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162165490167 apache2 fcntl < res=0(<f>/dev/null) 
1631268162165492596 apache2 setsockopt >
1631268162165494235 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162165494936 apache2 setsockopt >
1631268162165496156 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162165498041 apache2 poll > fds=12:431 timeout=1471228928 
1631268162165505377 mysqld poll < res=1 fds=20:41 
1631268162165507788 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268162165508157 mysqld fcntl < res=2(<p>pipe:[368952495]) 
1631268162165508396 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162165508561 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165508953 mysqld accept >
1631268162165513446 mysqld accept < fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) tuple=127.0.0.1:35130->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268162165514381 mysqld fcntl > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268162165514591 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165514745 mysqld fcntl > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162165514916 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165515522 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162165515694 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165515855 mysqld fcntl > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162165515988 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165540371 mysqld fcntl > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162165540746 mysqld fcntl < res=0(<f>/dev/null) 
1631268162165541059 mysqld setsockopt >
1631268162165542618 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268162165543309 mysqld setsockopt >
1631268162165543698 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162165545224 mysqld futex > addr=562726CC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268162165549962 mysqld futex < res=1 
1631268162165551147 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268162165840320 mysqld futex < res=0 
1631268162165842266 mysqld futex > addr=562726CBEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268162165842645 mysqld futex < res=0 
1631268162165843488 mysqld gettid >
1631268162165844290 mysqld gettid <
1631268162165849098 mysqld getpeername >
1631268162165850971 mysqld getpeername <
1631268162165859588 mysqld setsockopt >
1631268162165860712 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162165865679 mysqld sendto > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=102 tuple=NULL 
1631268162165886025 apache2 poll < res=1 fds=12:41 
1631268162165887335 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165888542 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAvQAAAEwmd0c6LncwAP/3LQIAP6AVAAAAAAAAAAAAACZqZkJUYm18SDNmKQA= 
1631268162165888837 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268162165890087 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165890900 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162165891530 apache2 poll > fds=12:431 timeout=1471228928 
1631268162165892316 mysqld poll > fds=41:43 timeout=10000 
1631268162165892331 apache2 poll < res=1 fds=12:41 
1631268162165892596 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=102 
1631268162165893632 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC9AAAATCZ3RzoudzAA//ctAgA/oBUAAAAAAAAAAAAAJmpmQlRibXxIM2YpAG15c3E= tuple=NULL 
1631268162165904126 apache2 sendto > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=106 tuple=NULL 
1631268162165920614 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABRdYg9YQcVQU/pDK52hEh8Xo9WRLgBteXNxbF9uYXRpdmVfcGFzc3c= 
1631268162165921087 mysqld poll < res=1 fds=41:41 
1631268162165922035 apache2 poll > fds=12:431 timeout=1471228928 
1631268162165922656 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165923888 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631268162165924599 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=102 
1631268162165925460 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFF1iD1hBxVBT+kMrnaESHxej1ZEuAG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631268162165931038 mysqld sendto > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=48 tuple=NULL 
1631268162165944825 apache2 poll < res=1 fds=12:41 
1631268162165945378 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165945858 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQATCZ3RzoudzAmamZCVGJtfEgzZikA 
1631268162165946396 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631268162165946793 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165947417 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162165947607 apache2 poll > fds=12:431 timeout=1471228928 
1631268162165948133 apache2 poll < res=1 fds=12:41 
1631268162165948368 mysqld poll > fds=41:43 timeout=10000 
1631268162165948416 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=102 
1631268162165949306 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZABMJndHOi53MCZqZkJUYm18SDNmKQA= tuple=NULL 
1631268162165953661 apache2 sendto > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=24 tuple=NULL 
1631268162165965364 apache2 sendto < res=24 data=FAAAA11iD1hBxVBT+kMrnaESHxej1ZEu 
1631268162165965399 mysqld poll < res=1 fds=41:41 
1631268162165966194 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165966370 apache2 poll > fds=12:431 timeout=1471228928 
1631268162165966912 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631268162165967352 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=20 
1631268162165968230 mysqld recvfrom < res=20 data=XWIPWEHFUFP6QyudoRIfF6PVkS4= tuple=NULL 
1631268162165974830 mysqld sendto > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=11 tuple=NULL 
1631268162165985057 apache2 poll < res=1 fds=12:41 
1631268162165985415 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631268162165985558 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=58 
1631268162165986886 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631268162165990214 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162165990961 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162165991438 mysqld poll > fds=41:43 timeout=28800000 
1631268162165998171 apache2 sendto > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=13 tuple=NULL 
1631268162166009983 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631268162166011814 apache2 poll > fds=12:431 timeout=1471228928 
1631268162166016557 mysqld poll < res=1 fds=41:41 
1631268162166017813 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162166018990 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631268162166020013 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=9 
1631268162166020770 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631268162166037590 mysqld access > mode=0(F_OK) 
1631268162166044981 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268162166051288 mysqld sendto > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=11 tuple=NULL 
1631268162166064250 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631268162166065010 apache2 poll < res=1 fds=12:41 
1631268162166066169 apache2 recvfrom > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=47 
1631268162166067737 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162166067781 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631268162166068264 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162166068880 mysqld poll > fds=41:43 timeout=28800000 
1631268162166093101 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631268162166099943 apache2 socket < fd=13(<4>) 
1631268162166100316 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631268162166100604 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631268162166100784 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631268162166100955 apache2 fcntl < res=0(<f>/dev/null) 
1631268162166101091 apache2 connect > fd=13(<4>) 
1631268162166130432 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:35132->127.0.0.1:3306 
1631268162166131542 apache2 poll > fds=13:435 timeout=60000 
1631268162166132418 apache2 poll < res=1 fds=13:44 
1631268162166132937 apache2 getsockopt >
1631268162166133592 mysqld poll < res=1 fds=20:41 
1631268162166133795 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631268162166134957 apache2 fcntl > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162166135229 apache2 fcntl < res=0(<f>/dev/null) 
1631268162166135232 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631268162166135657 mysqld fcntl < res=2(<p>pipe:[368952495]) 
1631268162166135888 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162166136140 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166136422 apache2 setsockopt >
1631268162166136601 mysqld accept >
1631268162166137025 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162166137338 apache2 setsockopt >
1631268162166137994 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162166138765 apache2 poll > fds=13:431 timeout=1471228928 
1631268162166142677 mysqld accept < fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) tuple=127.0.0.1:35132->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631268162166143646 mysqld fcntl > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) cmd=2(F_GETFD) 
1631268162166143868 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166144071 mysqld fcntl > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162166144267 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166144640 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162166144829 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166145024 mysqld fcntl > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) cmd=3(F_SETFD) 
1631268162166145185 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166161347 mysqld fcntl > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) cmd=5(F_SETFL) 
1631268162166161719 mysqld fcntl < res=0(<f>/dev/null) 
1631268162166161984 mysqld setsockopt >
1631268162166163197 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631268162166163714 mysqld setsockopt >
1631268162166164162 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631268162166165010 mysqld futex > addr=562726CC1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631268162166168547 mysqld futex < res=1 
1631268162166169090 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631268162166173084 mysqld futex < res=0 
1631268162166173953 mysqld futex > addr=562726CBEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631268162166174274 mysqld futex < res=0 
1631268162166174783 mysqld gettid >
1631268162166175945 mysqld gettid <
1631268162166177714 mysqld getpeername >
1631268162166178650 mysqld getpeername <
1631268162166182979 mysqld setsockopt >
1631268162166184020 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631268162166186657 mysqld sendto > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=102 tuple=NULL 
1631268162166208509 apache2 poll < res=1 fds=13:41 
1631268162166209783 apache2 recvfrom > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=4 
1631268162166211050 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631268162166213344 apache2 poll > fds=13:431 timeout=1471228928 
1631268162166214174 apache2 poll < res=1 fds=13:41 
1631268162166214424 apache2 recvfrom > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=102 
1631268162166215302 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC+AAAAN1tDfnE8dl8A//ctAgA/oBUAAAAAAAAAAAAAVnRle1w5SD49VnspAG15c3E= tuple=NULL 
1631268162166221513 apache2 sendto > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=110 tuple=NULL 
1631268162166229776 apache2 sendto < res=110 data=agAAAY2iCwAAAADAIQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABQ0quPbuc837tTQ6OxCj1/KWtELnmR2d2EAbXlzcWxfbmF0aXZlX3A= 
1631268162166230983 apache2 poll > fds=13:431 timeout=1471228928 
1631268162166242870 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAvgAAADdbQ35xPHZfAP/3LQIAP6AVAAAAAAAAAAAAAFZ0ZXtcOUg+PVZ7KQA= 
1631268162166244495 mysqld recvfrom > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=4 
1631268162166245644 mysqld recvfrom < res=4 data=agAAAQ== tuple=NULL 
1631268162166246158 mysqld recvfrom > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=106 
1631268162166246809 mysqld recvfrom < res=106 data=jaILAAAAAMAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFDSq49u5zzfu1NDo7EKPX8pa0QueZHZ3YQBteXNxbF9uYXRpdmVfcGFzc3c= tuple=NULL 
1631268162166255778 mysqld access > mode=0(F_OK) 
1631268162166261516 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631268162166264406 mysqld sendto > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=11 tuple=NULL 
1631268162166279229 apache2 poll < res=1 fds=13:41 
1631268162166280226 apache2 recvfrom > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=4 
1631268162166281471 apache2 recvfrom < res=4 data=BwAAAg== tuple=NULL 
1631268162166283000 apache2 poll > fds=13:431 timeout=1471228928 
1631268162166283726 apache2 poll < res=1 fds=13:41 
1631268162166283961 apache2 recvfrom > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=102 
1631268162166284772 apache2 recvfrom < res=7 data=AAAAAgAAAA== tuple=NULL 
1631268162166310502 apache2 nanosleep > interval=0(0s) 
1631268162166315078 mysqld sendto < res=11 data=BwAAAgAAAAIAAAA= 
1631268162166318440 mysqld recvfrom > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=4 
1631268162166319354 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631268162166320090 mysqld poll > fds=74:43 timeout=28800000 
1631268162166368080 apache2 nanosleep < res=0 
1631268162166381565 apache2 chdir >
1631268162166384213 apache2 chdir < res=0 path=/ 
1631268162166390961 apache2 sendto > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) size=5 tuple=NULL 
1631268162166407294 apache2 sendto < res=5 data=AQAAAAE= 
1631268162166407437 mysqld poll < res=1 fds=41:41 
1631268162166408995 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=4 
1631268162166409306 apache2 close > fd=12(<4t>127.0.0.1:35130->127.0.0.1:3306) 
1631268162166409961 apache2 close < res=0 
1631268162166410255 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268162166411122 mysqld recvfrom > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) size=1 
1631268162166412124 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268162166415805 mysqld shutdown > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268162166431615 apache2 setitimer >
1631268162166433057 apache2 setitimer <
1631268162166438292 mysqld shutdown < res=0 
1631268162166438992 mysqld close > fd=41(<4t>127.0.0.1:35130->127.0.0.1:3306) 
1631268162166439430 mysqld close < res=0 
1631268162166443570 apache2 ftruncate >
1631268162166457138 mysqld futex > addr=562726CC1364 op=128(FUTEX_PRIVATE_FLAG) val=371 
1631268162166477575 apache2 ftruncate <
1631268162166478242 apache2 pwrite > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) size=86 pos=0 
1631268162166489017 apache2 pwrite < res=86 data=ZHZ3YXxhOjE6e3M6ODoibWVzc2FnZXMiO2E6MDp7fX1zZXNzaW9uX3Rva2VufHM6MzI6ImIxNzc4Y2E1N2ZiNzkwMjJmMmU2YTA2NTVlOTY= 
1631268162166489891 apache2 close > fd=11(<f>/var/lib/php/sessions/sess_jrki3m9aqnun0mj6qu061269c0) 
1631268162166490222 apache2 close < res=0 
1631268162166522393 apache2 sendto > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) size=5 tuple=NULL 
1631268162166544394 apache2 sendto < res=5 data=AQAAAAE= 
1631268162166546057 apache2 close > fd=13(<4t>127.0.0.1:35132->127.0.0.1:3306) 
1631268162166546405 apache2 close < res=0 
1631268162166571187 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162166573722 apache2 fcntl < res=0(<f>/dev/null) 
1631268162166580771 apache2 setitimer >
1631268162166581356 apache2 setitimer <
1631268162166589427 apache2 brk > addr=563D8EB6B000 
1631268162166592752 apache2 brk < res=563D8EB6B000 vm_size=374924 vm_rss=15740 vm_swap=0 
1631268162166663832 apache2 brk > addr=563D8EB2B000 
1631268162166671321 apache2 brk < res=563D8EB2B000 vm_size=374668 vm_rss=15740 vm_swap=0 
1631268162166689195 apache2 read > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=8000 
1631268162166691552 apache2 read < res=-11(EAGAIN) data= 
1631268162166694287 apache2 writev > fd=10(<4t>192.168.64.12:35812->192.168.64.19:80) size=1075 
1631268162166734311 apache2 writev < res=1075 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjAyOjQyIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631268162166743550 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=233 
1631268162166751027 apache2 write < res=233 data=MTkyLjE2OC42NC4xMiAtIC0gWzEwL1NlcC8yMDIxOjEwOjAyOjQyICswMDAwXSAiR0VUIC9sb2dpbi5waHAgSFRUUC8xLjEiIDIwMCAxMDc= 
1631268162166751897 apache2 times >
1631268162166753586 apache2 times <
1631268162166759183 apache2 poll > fds=10:41 timeout=5000 
1631268162166765762 mysqld poll < res=1 fds=74:41 
1631268162166767143 mysqld recvfrom > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=4 
1631268162166768877 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631268162166769899 mysqld recvfrom > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) size=1 
1631268162166770751 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631268162166775437 mysqld shutdown > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631268162166793908 mysqld shutdown < res=0 
1631268162166794388 mysqld close > fd=74(<4t>127.0.0.1:35132->127.0.0.1:3306) 
1631268162166794795 mysqld close < res=0 
1631268162166804306 mysqld futex > addr=562726CC1364 op=128(FUTEX_PRIVATE_FLAG) val=372 
1631268162198319732 apache2 poll < res=1 fds=10:41 
1631268162198322409 apache2 read > fd=10(<4t>192.168.64.2:56892->192.168.64.19:80) size=8000 
1631268162198324891 apache2 read < res=562 data=R0VUIC92dWxuZXJhYmlsaXRpZXMveHNzX3IvIEhUVFAvMS4xDQpIb3N0OiAwMzE1ZmQyMjAwMGM0YmZiDQpDb25uZWN0aW9uOiBrZWVwLWE= 
1631268162198373019 apache2 stat >
1631268162198384751 apache2 stat < res=0 path=/var/www/html/vulnerabilities/xss_r/ 
1631268162198407248 apache2 stat >
1631268162198409768 apache2 stat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.html 
1631268162198411602 apache2 lstat >
1631268162198414166 apache2 lstat < res=0 path=/var 
1631268162198414920 apache2 lstat >
1631268162198416504 apache2 lstat < res=0 path=/var/www 
1631268162198417065 apache2 lstat >
1631268162198418729 apache2 lstat < res=0 path=/var/www/html 
1631268162198419173 apache2 lstat >
1631268162198420983 apache2 lstat < res=0 path=/var/www/html/vulnerabilities 
1631268162198421631 apache2 lstat >
1631268162198423472 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r 
1631268162198424214 apache2 lstat >
1631268162198425600 apache2 lstat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.html 
1631268162198437255 apache2 stat >
1631268162198439067 apache2 stat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.cgi 
1631268162198440202 apache2 lstat >
1631268162198441638 apache2 lstat < res=0 path=/var 
1631268162198442125 apache2 lstat >
1631268162198443315 apache2 lstat < res=0 path=/var/www 
1631268162198443854 apache2 lstat >
1631268162198445279 apache2 lstat < res=0 path=/var/www/html 
1631268162198445793 apache2 lstat >
1631268162198447312 apache2 lstat < res=0 path=/var/www/html/vulnerabilities 
1631268162198447955 apache2 lstat >
1631268162198449608 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r 
1631268162198450235 apache2 lstat >
1631268162198451523 apache2 lstat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.cgi 
1631268162198456390 apache2 stat >
1631268162198457985 apache2 stat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.pl 
1631268162198458872 apache2 lstat >
1631268162198460173 apache2 lstat < res=0 path=/var 
1631268162198460579 apache2 lstat >
1631268162198461846 apache2 lstat < res=0 path=/var/www 
1631268162198462300 apache2 lstat >
1631268162198463661 apache2 lstat < res=0 path=/var/www/html 
1631268162198464138 apache2 lstat >
1631268162198465655 apache2 lstat < res=0 path=/var/www/html/vulnerabilities 
1631268162198466215 apache2 lstat >
1631268162198467846 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r 
1631268162198468474 apache2 lstat >
1631268162198469655 apache2 lstat < res=-2(ENOENT) path=/var/www/html/vulnerabilities/xss_r/index.pl 
1631268162198474783 apache2 stat >
1631268162198477774 apache2 stat < res=0 path=/var/www/html/vulnerabilities/xss_r/index.php 
1631268162198510951 apache2 setitimer >
1631268162198511956 apache2 setitimer <
1631268162198512682 apache2 rt_sigaction >
1631268162198513205 apache2 rt_sigaction <
1631268162198514158 apache2 rt_sigprocmask >
1631268162198514549 apache2 rt_sigprocmask <
1631268162198536686 apache2 getcwd >
1631268162198537583 apache2 getcwd < res=2 path=/ 
1631268162198538612 apache2 chdir >
1631268162198540952 apache2 chdir < res=0 path=/var/www/html/vulnerabilities/xss_r 
1631268162198543303 apache2 setitimer >
1631268162198543619 apache2 setitimer <
1631268162198545572 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.3i6EOT (deleted)) cmd=8(F_SETLK) 
1631268162198555722 apache2 fcntl < res=0(<f>/dev/null) 
1631268162198564977 apache2 getcwd >
1631268162198565572 apache2 getcwd < res=36 path=/var/www/html/vulnerabilities/xss_r 
1631268162198596776 apache2 open >
1631268162198609780 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) name=/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501 flags=7(O_CREAT|O_RDWR) mode=0600 dev=200014 
1631268162198610879 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) 
1631268162198612528 apache2 fstat < res=0 
1631268162198613222 apache2 getuid >
1631268162198613936 apache2 getuid < uid=33(www-data) 
1631268162198614337 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) operation=2(LOCK_EX) 
1631268162198616750 apache2 flock < res=0 
1631268162198617125 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) cmd=3(F_SETFD) 
1631268162198617419 apache2 fcntl < res=0(<f>/dev/null) 
1631268162198617638 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) 
1631268162198618311 apache2 fstat < res=0 
1631268162198618653 apache2 pread > fd=11(<f>/var/lib/php/sessions/sess_rbkl9u171mbq4eh07ptvf9b501) size=115 pos=0 
1631268162198625916 apache2 pread < res=115 data=ZHZ3YXxhOjI6e3M6ODoibWVzc2FnZXMiO2E6MDp7fXM6ODoidXNlcm5hbWUiO3M6NzoiZ29yZG9uYiI7fXNlc3Npb25fdG9rZW58czozMjo= 
1631268162198639045 apache2 access > mode=0(F_OK) 
1631268162198645035 apache2 access < res=0 name=../../config/config.inc.php(/var/www/html/config/config.inc.php) 
1631268162198673994 apache2 getcwd >
1631268162198674786 apache2 getcwd < res=36 path=/var/www/html/vulnerabilities/xss_r 
1631268162198677870 apache2 lstat >
1631268162198683257 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r/../../hackable/uploads 
1631268162198684372 apache2 lstat >
1631268162198687034 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r/../../hackable 
1631268162198688029 apache2 lstat >
1631268162198689820 apache2 lstat < res=0 path=/var/www/html/vulnerabilities/xss_r 
