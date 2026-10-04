1631269680098522611 apache2 getsockname >
1631269680098523760 apache2 getsockname <
1631269680098531811 apache2 fcntl > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) cmd=4(F_GETFL) 
1631269680098532127 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680098532267 apache2 fcntl > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) cmd=5(F_SETFL) 
1631269680098532458 apache2 fcntl < res=0(<f>/dev/null) 
1631269680098556385 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680098558798 apache2 mmap < res=7F4A976EA000 vm_size=374020 vm_rss=9184 vm_swap=0 
1631269680098570354 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680098570957 apache2 mmap < res=7F4A976E8000 vm_size=374028 vm_rss=9184 vm_swap=0 
1631269680098572857 apache2 read > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=8000 
1631269680098575430 apache2 read < res=434 data=R0VUIC9sb2dpbi5waHAgSFRUUC8xLjENCkhvc3Q6IDQ2NTI3YmI5MjQ2MDE2ZTENCkNvbm5lY3Rpb246IGtlZXAtYWxpdmUNClVwZ3JhZGU= 
1631269680098623914 apache2 stat >
1631269680098631434 apache2 stat < res=0 path=/var/www/html/login.php 
1631269680098645703 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680098646842 apache2 mmap < res=7F4A976E6000 vm_size=374036 vm_rss=9184 vm_swap=0 
1631269680098733361 apache2 brk > addr=5585A22C0000 
1631269680098735706 apache2 brk < res=5585A22C0000 vm_size=374224 vm_rss=9184 vm_swap=0 
1631269680098889460 apache2 brk > addr=5585A22E1000 
1631269680098890506 apache2 brk < res=5585A22E1000 vm_size=374356 vm_rss=11096 vm_swap=0 
1631269680098918606 apache2 setitimer >
1631269680098920099 apache2 setitimer <
1631269680098920566 apache2 rt_sigaction >
1631269680098920945 apache2 rt_sigaction <
1631269680098921429 apache2 rt_sigprocmask >
1631269680098921607 apache2 rt_sigprocmask <
1631269680098970251 apache2 mmap > addr=0 length=65536 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680098971290 apache2 mmap < res=7F4A976D6000 vm_size=374420 vm_rss=11400 vm_swap=0 
1631269680098997466 apache2 getcwd >
1631269680098998148 apache2 getcwd < res=2 path=/ 
1631269680098998907 apache2 chdir >
1631269680099001047 apache2 chdir < res=0 path=/var/www/html 
1631269680099002786 apache2 setitimer >
1631269680099003013 apache2 setitimer <
1631269680099007025 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.5k3hzq (deleted)) cmd=8(F_SETLK) 
1631269680099009402 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099021342 apache2 lstat >
1631269680099023864 apache2 lstat < res=0 path=/var/www/html/login.php 
1631269680099024355 apache2 lstat >
1631269680099025699 apache2 lstat < res=0 path=/var/www/html 
1631269680099026054 apache2 lstat >
1631269680099027297 apache2 lstat < res=0 path=/var/www 
1631269680099027792 apache2 lstat >
1631269680099028879 apache2 lstat < res=0 path=/var 
1631269680099043820 apache2 stat >
1631269680099045341 apache2 stat < res=0 path=/var/www/html/login.php 
1631269680099066282 apache2 getcwd >
1631269680099066700 apache2 getcwd < res=14 path=/var/www/html 
1631269680099119282 apache2 getpid >
1631269680099119865 apache2 getpid <
1631269680099128472 apache2 open >
1631269680099135194 apache2 open < fd=11(<f>/dev/urandom) name=/dev/urandom flags=1(O_RDONLY) mode=0 dev=1000E4 
1631269680099138054 apache2 read > fd=11(<f>/dev/urandom) size=32 
1631269680099139054 apache2 read < res=32 data=rsZujA7pQTfdNznUb/lM/lnH+daz4s4QfQfOr/AipNA= 
1631269680099139847 apache2 close > fd=11(<f>/dev/urandom) 
1631269680099140172 apache2 close < res=0 
1631269680099143125 apache2 stat >
1631269680099158162 apache2 stat < res=-2(ENOENT) path=/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63 
1631269680099167814 apache2 open >
1631269680099188153 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) name=/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63 flags=7(O_CREAT|O_RDWR) mode=0600 dev=1000E0 
1631269680099189125 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) 
1631269680099189977 apache2 fstat < res=0 
1631269680099190290 apache2 getuid >
1631269680099190547 apache2 getuid < uid=33(www-data) 
1631269680099190814 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) operation=2(LOCK_EX) 
1631269680099192676 apache2 flock < res=0 
1631269680099192926 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) cmd=3(F_SETFD) 
1631269680099193203 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099193365 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) 
1631269680099193859 apache2 fstat < res=0 
1631269680099199001 apache2 access > mode=0(F_OK) 
1631269680099202212 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631269680099246136 apache2 getcwd >
1631269680099246740 apache2 getcwd < res=14 path=/var/www/html 
1631269680099247863 apache2 lstat >
1631269680099251553 apache2 lstat < res=0 path=/var/www/html/hackable/uploads 
1631269680099252099 apache2 lstat >
1631269680099253653 apache2 lstat < res=0 path=/var/www/html/hackable 
1631269680099254945 apache2 getcwd >
1631269680099255185 apache2 getcwd < res=14 path=/var/www/html 
1631269680099256096 apache2 lstat >
1631269680099260892 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631269680099261766 apache2 lstat >
1631269680099263893 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp 
1631269680099264515 apache2 lstat >
1631269680099266604 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS 
1631269680099267162 apache2 lstat >
1631269680099269146 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib 
1631269680099269728 apache2 lstat >
1631269680099271385 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6 
1631269680099271958 apache2 lstat >
1631269680099273847 apache2 lstat < res=0 path=/var/www/html/external/phpids 
1631269680099274423 apache2 lstat >
1631269680099275958 apache2 lstat < res=0 path=/var/www/html/external 
1631269680099278014 apache2 getcwd >
1631269680099278391 apache2 getcwd < res=14 path=/var/www/html 
1631269680099279148 apache2 lstat >
1631269680099281837 apache2 lstat < res=0 path=/var/www/html/config 
1631269680099295753 apache2 open >
1631269680099300828 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000E0 
1631269680099302426 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631269680099302787 apache2 lseek < res=0 
1631269680099303737 apache2 fstat > fd=12(<f>/etc/passwd) 
1631269680099304405 apache2 fstat < res=0 
1631269680099304706 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631269680099307022 apache2 mmap < res=7F4A97839000 vm_size=374424 vm_rss=13112 vm_swap=0 
1631269680099307291 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631269680099307713 apache2 lseek < res=1022 
1631269680099312546 apache2 munmap > addr=7F4A97839000 length=1022 
1631269680099314659 apache2 munmap < res=0 vm_size=374420 vm_rss=13932 vm_swap=0 
1631269680099314865 apache2 close > fd=12(<f>/etc/passwd) 
1631269680099315211 apache2 close < res=0 
1631269680099318585 apache2 access > mode=2(W_OK) 
1631269680099322189 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631269680099323258 apache2 access > mode=2(W_OK) 
1631269680099324481 apache2 access < res=0 name=/var/www/html/config 
1631269680099325119 apache2 access > mode=2(W_OK) 
1631269680099327016 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631269680099362913 apache2 socket > domain=10(AF_INET6) type=2 proto=0 
1631269680099367348 apache2 socket < fd=12(<6>) 
1631269680099370109 apache2 close > fd=12(<6>) 
1631269680099370311 apache2 close < res=0 
1631269680099375716 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631269680099378282 apache2 socket < fd=12(<4>) 
1631269680099378549 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631269680099378862 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680099378985 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631269680099379156 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099379273 apache2 connect > fd=12(<4>) 
1631269680099421492 mysqld poll < res=1 fds=20:41 
1631269680099424183 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631269680099424454 mysqld fcntl < res=2(<p>pipe:[371051682]) 
1631269680099424523 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:53978->127.0.0.1:3306 
1631269680099424669 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099424863 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099425212 mysqld accept >
1631269680099425731 apache2 poll > fds=12:435 timeout=60000 
1631269680099426629 apache2 poll < res=1 fds=12:44 
1631269680099426967 apache2 getsockopt >
1631269680099427573 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631269680099428051 apache2 fcntl > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099428306 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099430432 apache2 setsockopt >
1631269680099430584 mysqld accept < fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) tuple=127.0.0.1:53978->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631269680099431017 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680099431189 mysqld fcntl > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) cmd=2(F_GETFD) 
1631269680099431337 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099431381 apache2 setsockopt >
1631269680099431449 mysqld fcntl > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680099431581 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099431940 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680099432067 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099432178 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099432349 mysqld fcntl > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680099432453 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099433347 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099445610 mysqld fcntl > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099445804 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099445987 mysqld setsockopt >
1631269680099447043 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631269680099447410 mysqld setsockopt >
1631269680099447718 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680099448797 mysqld futex > addr=55B71A4C1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631269680099451601 mysqld futex < res=1 
1631269680099452145 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631269680099453955 mysqld futex < res=0 
1631269680099455815 mysqld futex > addr=55B71A4BEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631269680099456086 mysqld futex < res=0 
1631269680099456736 mysqld gettid >
1631269680099457104 mysqld gettid <
1631269680099459697 mysqld getpeername >
1631269680099461052 mysqld getpeername <
1631269680099467031 mysqld setsockopt >
1631269680099467912 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680099471564 mysqld sendto > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=102 tuple=NULL 
1631269680099503465 apache2 poll < res=1 fds=12:41 
1631269680099503815 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099504874 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631269680099506178 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAtQAAAFteSjZuS2pUAP/3LQIAP6AVAAAAAAAAAAAAAEQ2JVRWNUU8PFV6JgA= 
1631269680099507870 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099508547 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099509240 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099509750 apache2 poll < res=1 fds=12:41 
1631269680099509837 mysqld poll > fds=41:43 timeout=10000 
1631269680099509959 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=102 
1631269680099510903 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC1AAAAW15KNm5LalQA//ctAgA/oBUAAAAAAAAAAAAARDYlVFY1RTw8VXomAG15c3E= tuple=NULL 
1631269680099517479 apache2 sendto > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=106 tuple=NULL 
1631269680099530012 mysqld poll < res=1 fds=41:41 
1631269680099530611 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099530733 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABTaWBQmdg5ZAsFV4qRviLZGuogcegBteXNxbF9uYXRpdmVfcGFzc3c= 
1631269680099531550 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631269680099531961 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099531968 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=102 
1631269680099532832 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFNpYFCZ2DlkCwVXipG+Itka6iBx6AG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631269680099537076 mysqld sendto > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=48 tuple=NULL 
1631269680099545447 apache2 poll < res=1 fds=12:41 
1631269680099545660 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQAW15KNm5LalRENiVUVjVFPDxVeiYA 
1631269680099545787 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099546236 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099546455 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631269680099546562 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099546838 mysqld poll > fds=41:43 timeout=10000 
1631269680099547143 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099547439 apache2 poll < res=1 fds=12:41 
1631269680099547609 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=102 
1631269680099548146 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZABbXko2bktqVEQ2JVRWNUU8PFV6JgA= tuple=NULL 
1631269680099553132 apache2 sendto > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=24 tuple=NULL 
1631269680099561492 mysqld poll < res=1 fds=41:41 
1631269680099561654 apache2 sendto < res=24 data=FAAAA9pYFCZ2DlkCwVXipG+Itka6iBx6 
1631269680099561916 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099562393 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099562418 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631269680099562666 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=20 
1631269680099563160 mysqld recvfrom < res=20 data=2lgUJnYOWQLBVeKkb4i2RrqIHHo= tuple=NULL 
1631269680099567483 mysqld sendto > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=11 tuple=NULL 
1631269680099573682 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631269680099573860 apache2 poll < res=1 fds=12:41 
1631269680099574175 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=58 
1631269680099575242 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631269680099576507 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099576879 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099577152 mysqld poll > fds=41:43 timeout=28800000 
1631269680099590287 apache2 sendto > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=13 tuple=NULL 
1631269680099598382 mysqld poll < res=1 fds=41:41 
1631269680099598542 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631269680099598743 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099599296 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631269680099599749 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=9 
1631269680099599881 apache2 poll > fds=12:431 timeout=1471228928 
1631269680099600281 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631269680099611402 mysqld access > mode=0(F_OK) 
1631269680099617814 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631269680099622396 mysqld sendto > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=11 tuple=NULL 
1631269680099630639 apache2 poll < res=1 fds=12:41 
1631269680099630818 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631269680099630948 apache2 recvfrom > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=47 
1631269680099631987 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631269680099633444 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099633894 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099634206 mysqld poll > fds=41:43 timeout=28800000 
1631269680099651669 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631269680099655647 apache2 socket < fd=13(<4>) 
1631269680099655958 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631269680099656215 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680099656335 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631269680099656451 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099656583 apache2 connect > fd=13(<4>) 
1631269680099676103 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:53980->127.0.0.1:3306 
1631269680099676944 apache2 poll > fds=13:435 timeout=60000 
1631269680099677262 mysqld poll < res=1 fds=20:41 
1631269680099677579 apache2 poll < res=1 fds=13:44 
1631269680099677636 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631269680099677803 mysqld fcntl < res=2(<p>pipe:[371051682]) 
1631269680099677853 apache2 getsockopt >
1631269680099677937 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099678051 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099678201 mysqld accept >
1631269680099678371 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631269680099678712 apache2 fcntl > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099678913 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099679924 apache2 setsockopt >
1631269680099680133 mysqld accept < fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) tuple=127.0.0.1:53980->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631269680099680426 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680099680685 apache2 setsockopt >
1631269680099680711 mysqld fcntl > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) cmd=2(F_GETFD) 
1631269680099680911 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099681069 mysqld fcntl > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680099681075 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680099681230 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099681393 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099681527 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099681689 mysqld fcntl > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680099681767 apache2 poll > fds=13:431 timeout=1471228928 
1631269680099681833 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099690185 mysqld fcntl > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680099690445 mysqld fcntl < res=0(<f>/dev/null) 
1631269680099690632 mysqld setsockopt >
1631269680099691385 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631269680099691704 mysqld setsockopt >
1631269680099692043 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680099692649 mysqld futex > addr=55B71A4C1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631269680099694839 mysqld futex < res=1 
1631269680099695186 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631269680099697747 mysqld futex < res=0 
1631269680099698836 mysqld futex > addr=55B71A4BEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631269680099699107 mysqld futex < res=0 
1631269680099699590 mysqld gettid >
1631269680099699876 mysqld gettid <
1631269680099701376 mysqld getpeername >
1631269680099702391 mysqld getpeername <
1631269680099704887 mysqld setsockopt >
1631269680099705652 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680099707585 mysqld sendto > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=102 tuple=NULL 
1631269680099719333 apache2 poll < res=1 fds=13:41 
1631269680099719649 apache2 recvfrom > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099720492 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631269680099721248 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAtgAAAHFxY31pdjhRAP/3LQIAP6AVAAAAAAAAAAAAAHBfa3tJOSI9Sj86RgA= 
1631269680099721297 apache2 poll > fds=13:431 timeout=1471228928 
1631269680099721612 apache2 poll < res=1 fds=13:41 
1631269680099721781 apache2 recvfrom > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=102 
1631269680099722041 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099722473 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC2AAAAcXFjfWl2OFEA//ctAgA/oBUAAAAAAAAAAAAAcF9re0k5Ij1KPzpGAG15c3E= tuple=NULL 
1631269680099722620 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099723156 mysqld poll > fds=74:43 timeout=10000 
1631269680099726172 apache2 sendto > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=110 tuple=NULL 
1631269680099734924 mysqld poll < res=1 fds=74:41 
1631269680099735206 apache2 sendto < res=110 data=agAAAY2iCwAAAADAIQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABTGVOsMnP1i06DIMPm6p7MpSdmGYmR2d2EAbXlzcWxfbmF0aXZlX3A= 
1631269680099735469 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099735958 apache2 poll > fds=13:431 timeout=1471228928 
1631269680099736137 mysqld recvfrom < res=4 data=agAAAQ== tuple=NULL 
1631269680099736433 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=106 
1631269680099737034 mysqld recvfrom < res=106 data=jaILAAAAAMAhAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFMZU6wyc/WLToMgw+bqnsylJ2YZiZHZ3YQBteXNxbF9uYXRpdmVfcGFzc3c= tuple=NULL 
1631269680099742209 mysqld access > mode=0(F_OK) 
1631269680099746704 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631269680099748429 mysqld sendto > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=11 tuple=NULL 
1631269680099756306 apache2 poll < res=1 fds=13:41 
1631269680099756582 apache2 recvfrom > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099756643 mysqld sendto < res=11 data=BwAAAgAAAAIAAAA= 
1631269680099757249 apache2 recvfrom < res=4 data=BwAAAg== tuple=NULL 
1631269680099757862 apache2 poll > fds=13:431 timeout=1471228928 
1631269680099758170 apache2 poll < res=1 fds=13:41 
1631269680099758390 apache2 recvfrom > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=102 
1631269680099758717 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099758978 apache2 recvfrom < res=7 data=AAAAAgAAAA== tuple=NULL 
1631269680099759164 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680099759508 mysqld poll > fds=74:43 timeout=28800000 
1631269680099772857 apache2 nanosleep > interval=0(0s) 
1631269680099827291 apache2 nanosleep < res=0 
1631269680099846238 apache2 chdir >
1631269680099847703 apache2 chdir < res=0 path=/ 
1631269680099851659 apache2 sendto > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) size=5 tuple=NULL 
1631269680099861207 apache2 sendto < res=5 data=AQAAAAE= 
1631269680099861541 mysqld poll < res=1 fds=41:41 
1631269680099862375 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=4 
1631269680099862577 apache2 close > fd=12(<4t>127.0.0.1:53978->127.0.0.1:3306) 
1631269680099862938 apache2 close < res=0 
1631269680099863209 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631269680099863741 mysqld recvfrom > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) size=1 
1631269680099864343 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631269680099866847 mysqld shutdown > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631269680099874355 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680099876236 apache2 mmap < res=7F4A976D4000 vm_size=374428 vm_rss=13932 vm_swap=0 
1631269680099880414 mysqld shutdown < res=0 
1631269680099880839 mysqld close > fd=41(<4t>127.0.0.1:53978->127.0.0.1:3306) 
1631269680099881248 mysqld close < res=0 
1631269680099881427 apache2 setitimer >
1631269680099881867 apache2 setitimer <
1631269680099890891 mysqld futex > addr=55B71A4C1364 op=128(FUTEX_PRIVATE_FLAG) val=357 
1631269680099902083 apache2 pwrite > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) size=65 pos=0 
1631269680099914044 apache2 pwrite < res=65 data=ZHZ3YXxhOjA6e31zZXNzaW9uX3Rva2VufHM6MzI6IjlmYzNjZDExMzI4ZTk3NjUxYTIwZDBhZDY4NzE2MTAwIjs= 
1631269680099914697 apache2 close > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) 
1631269680099914982 apache2 close < res=0 
1631269680099920693 apache2 sendto > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) size=5 tuple=NULL 
1631269680099931040 apache2 sendto < res=5 data=AQAAAAE= 
1631269680099931116 mysqld poll < res=1 fds=74:41 
1631269680099931871 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=4 
1631269680099932027 apache2 close > fd=13(<4t>127.0.0.1:53980->127.0.0.1:3306) 
1631269680099932214 apache2 close < res=0 
1631269680099932748 mysqld recvfrom < res=4 data=AQAAAA== tuple=NULL 
1631269680099933267 mysqld recvfrom > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) size=1 
1631269680099933828 mysqld recvfrom < res=1 data=AQ== tuple=NULL 
1631269680099936145 mysqld shutdown > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) how=2(SHUT_RDWR) 
1631269680099945009 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.5k3hzq (deleted)) cmd=8(F_SETLK) 
1631269680099946591 apache2 fcntl < res=0(<f>/dev/null) 
1631269680099947688 mysqld shutdown < res=0 
1631269680099948065 mysqld close > fd=74(<4t>127.0.0.1:53980->127.0.0.1:3306) 
1631269680099948386 mysqld close < res=0 
1631269680099950934 apache2 setitimer >
1631269680099951196 apache2 setitimer <
1631269680099954955 mysqld futex > addr=55B71A4C1364 op=128(FUTEX_PRIVATE_FLAG) val=358 
1631269680099957397 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680099958924 apache2 mmap < res=7F4A976D2000 vm_size=374436 vm_rss=13932 vm_swap=0 
1631269680099967756 apache2 brk > addr=5585A2306000 
1631269680099968760 apache2 brk < res=5585A2306000 vm_size=374584 vm_rss=13932 vm_swap=0 
1631269680099971784 apache2 mmap > addr=0 length=135168 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680099972305 apache2 mmap < res=7F4A976B1000 vm_size=374716 vm_rss=13932 vm_swap=0 
1631269680100057819 apache2 munmap > addr=7F4A976B1000 length=135168 
1631269680100063959 apache2 munmap < res=0 vm_size=374584 vm_rss=14900 vm_swap=0 
1631269680100064567 apache2 brk > addr=5585A22E4000 
1631269680100071968 apache2 brk < res=5585A22E4000 vm_size=374448 vm_rss=14768 vm_swap=0 
1631269680100078051 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680100078965 apache2 mmap < res=7F4A976D0000 vm_size=374456 vm_rss=14768 vm_swap=0 
1631269680100087860 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680100088465 apache2 mmap < res=7F4A976CE000 vm_size=374464 vm_rss=14768 vm_swap=0 
1631269680100092624 apache2 read > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=8000 
1631269680100093930 apache2 read < res=-11(EAGAIN) data= 
1631269680100096817 apache2 writev > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=1192 
1631269680100120663 apache2 writev < res=1192 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjI4OjAwIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631269680100134449 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=195 
1631269680100140370 apache2 write < res=195 data=MTkyLjE2OC4xNzYuMTQgLSAtIFsxMC9TZXAvMjAyMToxMDoyODowMCArMDAwMF0gIkdFVCAvbG9naW4ucGhwIEhUVFAvMS4xIiAyMDAgMTE= 
1631269680100141158 apache2 times >
1631269680100142053 apache2 times <
1631269680100148185 apache2 poll > fds=10:41 timeout=5000 
1631269680111714240 apache2 poll < res=1 fds=10:41 
1631269680111716497 apache2 read > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=8000 
1631269680111718693 apache2 read < res=400 data=R0VUIC9kdndhL2Nzcy9sb2dpbi5jc3MgSFRUUC8xLjENCkhvc3Q6IDQ2NTI3YmI5MjQ2MDE2ZTENCkNvbm5lY3Rpb246IGtlZXAtYWxpdmU= 
1631269680111774160 apache2 stat >
1631269680111783100 apache2 stat < res=0 path=/var/www/html/dvwa/css/login.css 
1631269680111802843 apache2 open >
1631269680111809697 apache2 open < fd=11(<f>/var/www/html/dvwa/css/login.css) name=/var/www/html/dvwa/css/login.css flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000E0 
1631269680111817804 apache2 mmap > addr=0 length=842 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/css/login.css) offset=0 
1631269680111821431 apache2 mmap < res=7F4A97839000 vm_size=374468 vm_rss=14768 vm_swap=0 
1631269680111825525 apache2 brk > addr=5585A2306000 
1631269680111827207 apache2 brk < res=5585A2306000 vm_size=374604 vm_rss=14768 vm_swap=0 
1631269680111830787 apache2 brk > addr=5585A2346000 
1631269680111831097 apache2 brk < res=5585A2346000 vm_size=374860 vm_rss=14768 vm_swap=0 
1631269680111901688 apache2 munmap > addr=7F4A97839000 length=842 
1631269680111902878 apache2 accept < fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) tuple=192.168.176.14:43886->192.168.176.15:80 queuepct=0 queuelen=0 queuemax=511 
1631269680111904551 apache2 munmap < res=0 vm_size=374856 vm_rss=14988 vm_swap=0 
1631269680111910446 apache2 getsockname >
1631269680111911485 apache2 getsockname <
1631269680111918378 apache2 fcntl > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) cmd=4(F_GETFL) 
1631269680111918663 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680111918805 apache2 fcntl > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) cmd=5(F_SETFL) 
1631269680111918994 apache2 fcntl < res=0(<f>/dev/null) 
1631269680111940166 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680111943003 apache2 mmap < res=7F4A976EA000 vm_size=374020 vm_rss=9184 vm_swap=0 
1631269680111944651 apache2 brk > addr=5585A2306000 
1631269680111949024 apache2 brk < res=5585A2306000 vm_size=374600 vm_rss=14976 vm_swap=0 
1631269680111949399 apache2 brk > addr=5585A22E4000 
1631269680111952188 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680111952867 apache2 mmap < res=7F4A976E8000 vm_size=374028 vm_rss=9184 vm_swap=0 
1631269680111954343 apache2 read > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=8000 
1631269680111956043 apache2 brk < res=5585A22E4000 vm_size=374464 vm_rss=14844 vm_swap=0 
1631269680111957067 apache2 read < res=454 data=R0VUIC9kdndhL2ltYWdlcy9sb2dpbl9sb2dvLnBuZyBIVFRQLzEuMQ0KSG9zdDogNDY1MjdiYjkyNDYwMTZlMQ0KQ29ubmVjdGlvbjoga2U= 
1631269680111965973 apache2 read > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=8000 
1631269680111967107 apache2 read < res=-11(EAGAIN) data= 
1631269680111968727 apache2 writev > fd=10(<4t>192.168.176.14:43884->192.168.176.15:80) size=741 
1631269680111991309 apache2 writev < res=741 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjI4OjAwIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631269680111996694 apache2 stat >
1631269680111996749 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=235 
1631269680112002202 apache2 write < res=235 data=MTkyLjE2OC4xNzYuMTQgLSAtIFsxMC9TZXAvMjAyMToxMDoyODowMCArMDAwMF0gIkdFVCAvZHZ3YS9jc3MvbG9naW4uY3NzIEhUVFAvMS4= 
1631269680112003022 apache2 times >
1631269680112003376 apache2 stat < res=0 path=/var/www/html/dvwa/images/login_logo.png 
1631269680112004378 apache2 times <
1631269680112004717 apache2 close > fd=11(<f>/var/www/html/dvwa/css/login.css) 
1631269680112005055 apache2 close < res=0 
1631269680112008839 apache2 poll > fds=10:41 timeout=5000 
1631269680112011302 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680112012224 apache2 mmap < res=7F4A976E6000 vm_size=374036 vm_rss=9184 vm_swap=0 
1631269680112048397 apache2 open >
1631269680112054035 apache2 open < fd=11(<f>/var/www/html/dvwa/images/login_logo.png) name=/var/www/html/dvwa/images/login_logo.png flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000E0 
1631269680112063059 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680112063870 apache2 mmap < res=7F4A976E4000 vm_size=374044 vm_rss=9184 vm_swap=0 
1631269680112069546 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680112069990 apache2 mmap < res=7F4A976E2000 vm_size=374052 vm_rss=9184 vm_swap=0 
1631269680112071792 apache2 mmap > addr=0 length=9088 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/dvwa/images/login_logo.png) offset=0 
1631269680112073663 apache2 mmap < res=7F4A976DF000 vm_size=374064 vm_rss=9184 vm_swap=0 
1631269680112075344 apache2 writev > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=9375 
1631269680112120518 apache2 writev < res=9375 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjI4OjAwIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631269680112123355 apache2 munmap > addr=7F4A976DF000 length=9088 
1631269680112127204 apache2 munmap < res=0 vm_size=374052 vm_rss=10424 vm_swap=0 
1631269680112141424 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=244 
1631269680112147146 apache2 write < res=244 data=MTkyLjE2OC4xNzYuMTQgLSAtIFsxMC9TZXAvMjAyMToxMDoyODowMCArMDAwMF0gIkdFVCAvZHZ3YS9pbWFnZXMvbG9naW5fbG9nby5wbmc= 
1631269680112147921 apache2 times >
1631269680112148915 apache2 times <
1631269680112149343 apache2 close > fd=11(<f>/var/www/html/dvwa/images/login_logo.png) 
1631269680112149700 apache2 close < res=0 
1631269680112152898 apache2 read > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=8000 
1631269680112153782 apache2 read < res=-11(EAGAIN) data= 
1631269680112159394 apache2 poll > fds=10:41 timeout=5000 
1631269680130984537 apache2 poll < res=1 fds=10:41 
1631269680130986925 apache2 read > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=8000 
1631269680130989247 apache2 read < res=439 data=R0VUIC9mYXZpY29uLmljbyBIVFRQLzEuMQ0KSG9zdDogNDY1MjdiYjkyNDYwMTZlMQ0KQ29ubmVjdGlvbjoga2VlcC1hbGl2ZQ0KVXNlci0= 
1631269680131027556 apache2 stat >
1631269680131034642 apache2 stat < res=0 path=/var/www/html/favicon.ico 
1631269680131055442 apache2 open >
1631269680131062123 apache2 open < fd=11(<f>/var/www/html/favicon.ico) name=/var/www/html/favicon.ico flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000E0 
1631269680131079709 apache2 read > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=8000 
1631269680131080615 apache2 read < res=-11(EAGAIN) data= 
1631269680131082037 apache2 mmap > addr=0 length=1406 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=11(<f>/var/www/html/favicon.ico) offset=0 
1631269680131086364 apache2 mmap < res=7F4A97839000 vm_size=374056 vm_rss=10424 vm_swap=0 
1631269680131087172 apache2 writev > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=1706 
1631269680131114887 apache2 writev < res=1706 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjI4OjAwIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631269680131116269 apache2 munmap > addr=7F4A97839000 length=1406 
1631269680131119798 apache2 munmap < res=0 vm_size=374052 vm_rss=10488 vm_swap=0 
1631269680131123969 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=229 
1631269680131129347 apache2 write < res=229 data=MTkyLjE2OC4xNzYuMTQgLSAtIFsxMC9TZXAvMjAyMToxMDoyODowMCArMDAwMF0gIkdFVCAvZmF2aWNvbi5pY28gSFRUUC8xLjEiIDIwMCA= 
1631269680131130179 apache2 times >
1631269680131131540 apache2 times <
1631269680131132442 apache2 close > fd=11(<f>/var/www/html/favicon.ico) 
1631269680131132720 apache2 close < res=0 
1631269680131136180 apache2 poll > fds=10:41 timeout=5000 
1631269680145917612 mysqld io_getevents <
1631269680145920486 mysqld io_getevents >
1631269680187416284 apache2 select < res=0 
1631269680187420049 apache2 write > fd=5(<p>pipe:[371051716]) size=1 
1631269680187421870 apache2 write < res=1 data=IQ== 
1631269680187425047 apache2 socket > domain=2(AF_INET) type=524289 proto=0 
1631269680187432608 apache2 socket < fd=9(<4>) 
1631269680187433370 apache2 fcntl > fd=9(<4>) cmd=4(F_GETFL) 
1631269680187433742 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680187433862 apache2 fcntl > fd=9(<4>) cmd=5(F_SETFL) 
1631269680187434006 apache2 fcntl < res=0(<f>/dev/null) 
1631269680187434393 apache2 connect > fd=9(<4>) 
1631269680187495098 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:59376->0.0.0.0:80 
1631269680187496977 apache2 poll > fds=9:44 timeout=3000 
1631269680187497802 apache2 poll < res=1 fds=9:44 
1631269680187498117 apache2 getsockopt >
1631269680187498949 apache2 getsockopt < res=0 fd=9(<4t>127.0.0.1:59376->0.0.0.0:80) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631269680187516236 apache2 write > fd=9(<4t>127.0.0.1:59376->0.0.0.0:80) size=86 
1631269680187541921 apache2 write < res=86 data=T1BUSU9OUyAqIEhUVFAvMS4wDQpVc2VyLUFnZW50OiBBcGFjaGUvMi40LjI1IChEZWJpYW4pIChpbnRlcm5hbCBkdW1teSBjb25uZWN0aW8= 
1631269680187542685 apache2 close > fd=9(<4t>127.0.0.1:59376->0.0.0.0:80) 
1631269680187543016 apache2 close < res=0 
1631269680187550936 apache2 wait4 >
1631269680187559616 apache2 wait4 <
1631269680187561723 apache2 wait4 >
1631269680187563264 apache2 wait4 <
1631269680187563550 apache2 select >
1631269680187572534 apache2 accept < fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) tuple=127.0.0.1:59376->127.0.0.1:80 queuepct=0 queuelen=0 queuemax=511 
1631269680187580555 apache2 getsockname >
1631269680187581495 apache2 getsockname <
1631269680187589148 apache2 fcntl > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) cmd=4(F_GETFL) 
1631269680187589441 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680187589570 apache2 fcntl > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) cmd=5(F_SETFL) 
1631269680187589732 apache2 fcntl < res=0(<f>/dev/null) 
1631269680187594359 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680187597005 apache2 mmap < res=7F4A976EA000 vm_size=374020 vm_rss=9184 vm_swap=0 
1631269680187607189 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680187607860 apache2 mmap < res=7F4A976E8000 vm_size=374028 vm_rss=9184 vm_swap=0 
1631269680187609441 apache2 read > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) size=8000 
1631269680187611923 apache2 read < res=86 data=T1BUSU9OUyAqIEhUVFAvMS4wDQpVc2VyLUFnZW50OiBBcGFjaGUvMi40LjI1IChEZWJpYW4pIChpbnRlcm5hbCBkdW1teSBjb25uZWN0aW8= 
1631269680187655438 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680187656254 apache2 mmap < res=7F4A976E6000 vm_size=374036 vm_rss=9184 vm_swap=0 
1631269680187665203 apache2 mmap > addr=0 length=8192 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680187665739 apache2 mmap < res=7F4A976E4000 vm_size=374044 vm_rss=9184 vm_swap=0 
1631269680187669357 apache2 writev > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) size=126 
1631269680187691734 apache2 writev < res=126 data=SFRUUC8xLjEgMjAwIE9LDQpEYXRlOiBGcmksIDEwIFNlcCAyMDIxIDEwOjI4OjAwIEdNVA0KU2VydmVyOiBBcGFjaGUvMi40LjI1IChEZWI= 
1631269680187706546 apache2 write > fd=7(<f>/var/log/apache2/access.log) size=129 
1631269680187718199 apache2 write < res=129 data=MTI3LjAuMC4xIC0gLSBbMTAvU2VwLzIwMjE6MTA6Mjg6MDAgKzAwMDBdICJPUFRJT05TICogSFRUUC8xLjAiIDIwMCAxMjYgIi0iICJBcGE= 
1631269680187719051 apache2 times >
1631269680187720086 apache2 times <
1631269680187723509 apache2 shutdown > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) how=1(SHUT_WR) 
1631269680187724204 apache2 shutdown < res=-107(ENOTCONN) 
1631269680187724673 apache2 close > fd=10(<4t>127.0.0.1:59376->127.0.0.1:80) 
1631269680187724932 apache2 close < res=0 
1631269680187728671 apache2 read > fd=4(<p>pipe:[371051716]) size=1 
1631269680187729956 apache2 read < res=1 data=IQ== 
1631269680187731417 apache2 close > fd=9 
1631269680187731690 apache2 close < res=0 
1631269680188284551 apache2 munmap > addr=7F4A80AEF000 length=67108864 
1631269680188292462 apache2 munmap < res=0 vm_size=308508 vm_rss=10692 vm_swap=0 
1631269680188294363 apache2 close > fd=8(<f>/tmp/.ZendSem.5k3hzq (deleted)) 
1631269680188294937 apache2 close < res=0 
1631269680188416361 apache2 munmap > addr=7F4A85468000 length=2126312 
1631269680188423587 apache2 munmap < res=0 vm_size=306428 vm_rss=11532 vm_swap=0 
1631269680188424280 apache2 munmap > addr=7F4A85252000 length=2183192 
1631269680188429667 apache2 munmap < res=0 vm_size=304292 vm_rss=11444 vm_swap=0 
1631269680188430121 apache2 munmap > addr=7F4A85013000 length=2352488 
1631269680188435869 apache2 munmap < res=0 vm_size=301992 vm_rss=11244 vm_swap=0 
1631269680188436268 apache2 munmap > addr=7F4A84D03000 length=3208448 
1631269680188443057 apache2 munmap < res=0 vm_size=298856 vm_rss=11080 vm_swap=0 
1631269680188443411 apache2 munmap > addr=7F4A84AEF000 length=2175160 
1631269680188448312 apache2 munmap < res=0 vm_size=296728 vm_rss=11008 vm_swap=0 
1631269680188463228 apache2 munmap > addr=7F4A85670000 length=2142720 
1631269680188468016 apache2 munmap < res=0 vm_size=294632 vm_rss=10992 vm_swap=0 
1631269680188480129 apache2 munmap > addr=7F4A8587C000 length=2130472 
1631269680188484392 apache2 munmap < res=0 vm_size=292548 vm_rss=10984 vm_swap=0 
1631269680188493779 apache2 munmap > addr=7F4A85A85000 length=2126032 
1631269680188498258 apache2 munmap < res=0 vm_size=290468 vm_rss=10976 vm_swap=0 
1631269680188506399 apache2 munmap > addr=7F4A85C8D000 length=2113776 
1631269680188510845 apache2 munmap < res=0 vm_size=288400 vm_rss=10968 vm_swap=0 
1631269680188518740 apache2 munmap > addr=7F4A85E92000 length=2109680 
1631269680188522927 apache2 munmap < res=0 vm_size=286336 vm_rss=10960 vm_swap=0 
1631269680188530789 apache2 munmap > addr=7F4A86096000 length=2105552 
1631269680188534977 apache2 munmap < res=0 vm_size=284276 vm_rss=10952 vm_swap=0 
1631269680188542718 apache2 munmap > addr=7F4A86299000 length=2113744 
1631269680188546534 apache2 munmap < res=0 vm_size=282208 vm_rss=10944 vm_swap=0 
1631269680188557242 apache2 munmap > addr=7F4A8649E000 length=2183504 
1631269680188561883 apache2 munmap < res=0 vm_size=280072 vm_rss=10932 vm_swap=0 
1631269680188571143 apache2 munmap > addr=7F4A866B4000 length=2150936 
1631269680188575834 apache2 munmap < res=0 vm_size=277968 vm_rss=10924 vm_swap=0 
1631269680188583411 apache2 munmap > addr=7F4A868C2000 length=2109656 
1631269680188587061 apache2 munmap < res=0 vm_size=275904 vm_rss=10916 vm_swap=0 
1631269680188778394 apache2 munmap > addr=7F4A8714B000 length=2126152 
1631269680188783944 apache2 munmap < res=0 vm_size=273824 vm_rss=15020 vm_swap=0 
1631269680188784442 apache2 munmap > addr=7F4A86F13000 length=2322976 
1631269680188790364 apache2 munmap < res=0 vm_size=271552 vm_rss=14884 vm_swap=0 
1631269680188790701 apache2 munmap > addr=7F4A86CF0000 length=2236808 
1631269680188795716 apache2 munmap < res=0 vm_size=269364 vm_rss=14752 vm_swap=0 
1631269680188796141 apache2 munmap > addr=7F4A86AC6000 length=2267936 
1631269680188801308 apache2 munmap < res=0 vm_size=267148 vm_rss=14628 vm_swap=0 
1631269680188809320 apache2 munmap > addr=7F4A87353000 length=2130320 
1631269680188813485 apache2 munmap < res=0 vm_size=265064 vm_rss=14592 vm_swap=0 
1631269680188827461 apache2 munmap > addr=7F4A8755C000 length=2381440 
1631269680188834128 apache2 munmap < res=0 vm_size=262736 vm_rss=14576 vm_swap=0 
1631269680188849780 apache2 munmap > addr=7F4A877A2000 length=2236896 
1631269680188855446 apache2 munmap < res=0 vm_size=260548 vm_rss=14492 vm_swap=0 
1631269680188985700 apache2 munmap > addr=7F4A8A31A000 length=2138688 
1631269680188992552 apache2 munmap < res=0 vm_size=258456 vm_rss=15628 vm_swap=0 
1631269680188993093 apache2 munmap > addr=7F4A8A0E9000 length=2294064 
1631269680188999005 apache2 munmap < res=0 vm_size=256212 vm_rss=15488 vm_swap=0 
1631269680188999423 apache2 munmap > addr=7F4A89E9E000 length=2401248 
1631269680189005710 apache2 munmap < res=0 vm_size=253864 vm_rss=15344 vm_swap=0 
1631269680189006354 apache2 munmap > addr=7F4A89C4D000 length=2427528 
1631269680189012750 apache2 munmap < res=0 vm_size=251492 vm_rss=15204 vm_swap=0 
1631269680189014603 apache2 munmap > addr=7F4A89973000 length=2988384 
1631269680189021983 apache2 munmap < res=0 vm_size=248572 vm_rss=14948 vm_swap=0 
1631269680189022375 apache2 munmap > addr=7F4A89740000 length=2302456 
1631269680189028477 apache2 munmap < res=0 vm_size=246320 vm_rss=14816 vm_swap=0 
1631269680189029024 apache2 munmap > addr=7F4A8953C000 length=2109608 
1631269680189033027 apache2 munmap < res=0 vm_size=244256 vm_rss=14796 vm_swap=0 
1631269680189033324 apache2 munmap > addr=7F4A89330000 length=2143528 
1631269680189037993 apache2 munmap < res=0 vm_size=242160 vm_rss=14748 vm_swap=0 
1631269680189038330 apache2 munmap > addr=7F4A8912C000 length=2109456 
1631269680189042378 apache2 munmap < res=0 vm_size=240096 vm_rss=14728 vm_swap=0 
1631269680189042703 apache2 munmap > addr=7F4A88F1D000 length=2154920 
1631269680189046776 apache2 munmap < res=0 vm_size=237988 vm_rss=14672 vm_swap=0 
1631269680189047271 apache2 munmap > addr=7F4A88D02000 length=2204648 
1631269680189052691 apache2 munmap < res=0 vm_size=235832 vm_rss=14560 vm_swap=0 
1631269680189053077 apache2 munmap > addr=7F4A88969000 length=3771208 
1631269680189063762 apache2 munmap < res=0 vm_size=232148 vm_rss=13924 vm_swap=0 
1631269680189064180 apache2 munmap > addr=7F4A88704000 length=2507952 
1631269680189071134 apache2 munmap < res=0 vm_size=229696 vm_rss=13648 vm_swap=0 
1631269680189071495 apache2 munmap > addr=7F4A884D0000 length=2306096 
1631269680189076234 apache2 munmap < res=0 vm_size=227440 vm_rss=13580 vm_swap=0 
1631269680189076625 apache2 munmap > addr=7F4A882BD000 length=2171592 
1631269680189080865 apache2 munmap < res=0 vm_size=225316 vm_rss=13508 vm_swap=0 
1631269680189081225 apache2 munmap > addr=7F4A87E51000 length=2311792 
1631269680189086354 apache2 munmap < res=0 vm_size=223056 vm_rss=13376 vm_swap=0 
1631269680189086714 apache2 munmap > addr=7F4A88086000 length=2319552 
1631269680189092158 apache2 munmap < res=0 vm_size=220788 vm_rss=13236 vm_swap=0 
1631269680189092525 apache2 munmap > addr=7F4A87BCE000 length=2632576 
1631269680189097841 apache2 munmap < res=0 vm_size=218216 vm_rss=13100 vm_swap=0 
1631269680189098255 apache2 munmap > addr=7F4A879C5000 length=2131560 
1631269680189102073 apache2 munmap < res=0 vm_size=216132 vm_rss=13064 vm_swap=0 
1631269680189110034 apache2 munmap > addr=7F4A8A525000 length=2126312 
1631269680189114676 apache2 munmap < res=0 vm_size=214052 vm_rss=13032 vm_swap=0 
1631269680189130148 apache2 munmap > addr=7F4A8A72D000 length=2238728 
1631269680189135372 apache2 munmap < res=0 vm_size=211864 vm_rss=12948 vm_swap=0 
1631269680189140888 apache2 munmap > addr=7F4A8A950000 length=2134248 
1631269680189145246 apache2 munmap < res=0 vm_size=209776 vm_rss=12904 vm_swap=0 
1631269680189152100 apache2 munmap > addr=7F4A8AB5A000 length=2138392 
1631269680189156119 apache2 munmap < res=0 vm_size=207684 vm_rss=12860 vm_swap=0 
1631269680189161991 apache2 munmap > addr=7F4A8AD65000 length=2109648 
1631269680189165480 apache2 munmap < res=0 vm_size=205620 vm_rss=12840 vm_swap=0 
1631269680189237836 apache2 munmap > addr=7F4A8CFDB000 length=2199768 
1631269680189247552 apache2 munmap < res=0 vm_size=203468 vm_rss=13416 vm_swap=0 
1631269680189248062 apache2 munmap > addr=7F4A8CD74000 length=2517896 
1631269680189255070 apache2 munmap < res=0 vm_size=201008 vm_rss=13204 vm_swap=0 
1631269680189255438 apache2 munmap > addr=7F4A8C822000 length=2168016 
1631269680189259965 apache2 munmap < res=0 vm_size=198888 vm_rss=13136 vm_swap=0 
1631269680189260369 apache2 munmap > addr=7F4A8CA34000 length=3407224 
1631269680189266142 apache2 munmap < res=0 vm_size=195560 vm_rss=12920 vm_swap=0 
1631269680189266528 apache2 munmap > addr=7F4A8C123000 length=2494200 
1631269680189272778 apache2 munmap < res=0 vm_size=193124 vm_rss=12788 vm_swap=0 
1631269680189273140 apache2 munmap > addr=7F4A8BC36000 length=2348648 
1631269680189278892 apache2 munmap < res=0 vm_size=190828 vm_rss=12648 vm_swap=0 
1631269680189279215 apache2 munmap > addr=7F4A8BE74000 length=2811792 
1631269680189285368 apache2 munmap < res=0 vm_size=188080 vm_rss=12452 vm_swap=0 
1631269680189285739 apache2 munmap > addr=7F4A8C5EF000 length=2301968 
1631269680189291151 apache2 munmap < res=0 vm_size=185828 vm_rss=12320 vm_swap=0 
1631269680189291565 apache2 munmap > addr=7F4A8B9BF000 length=2581488 
1631269680189296906 apache2 munmap < res=0 vm_size=183304 vm_rss=12180 vm_swap=0 
1631269680189297262 apache2 munmap > addr=7F4A8C384000 length=2531352 
1631269680189302388 apache2 munmap < res=0 vm_size=180828 vm_rss=12052 vm_swap=0 
1631269680189302720 apache2 munmap > addr=7F4A8B797000 length=2258056 
1631269680189307348 apache2 munmap < res=0 vm_size=178620 vm_rss=11928 vm_swap=0 
1631269680189307721 apache2 munmap > addr=7F4A8B589000 length=2153448 
1631269680189311643 apache2 munmap < res=0 vm_size=176516 vm_rss=11872 vm_swap=0 
1631269680189311939 apache2 munmap > addr=7F4A8B385000 length=2109744 
1631269680189315647 apache2 munmap < res=0 vm_size=174452 vm_rss=11852 vm_swap=0 
1631269680189315990 apache2 munmap > addr=7F4A8B17F000 length=2117872 
1631269680189319535 apache2 munmap < res=0 vm_size=172380 vm_rss=11824 vm_swap=0 
1631269680189319854 apache2 munmap > addr=7F4A8AF69000 length=2183248 
1631269680189324505 apache2 munmap < res=0 vm_size=170244 vm_rss=11744 vm_swap=0 
1631269680189331449 apache2 munmap > addr=7F4A8D1F5000 length=2154704 
1631269680189335768 apache2 munmap < res=0 vm_size=168136 vm_rss=11692 vm_swap=0 
1631269680189342244 apache2 munmap > addr=7F4A8D404000 length=5264896 
1631269680189347824 apache2 munmap < res=0 vm_size=162992 vm_rss=11620 vm_swap=0 
1631269680189354008 apache2 munmap > addr=7F4A8D90A000 length=2158896 
1631269680189358520 apache2 munmap < res=0 vm_size=160880 vm_rss=11556 vm_swap=0 
1631269680189372816 apache2 munmap > addr=7F4A8DB1A000 length=2292264 
1631269680189378356 apache2 munmap < res=0 vm_size=158640 vm_rss=11468 vm_swap=0 
1631269680189383106 apache2 munmap > addr=7F4A8DD4A000 length=2109648 
1631269680189387251 apache2 munmap < res=0 vm_size=156576 vm_rss=11448 vm_swap=0 
1631269680189392033 apache2 munmap > addr=7F4A8DF4E000 length=2131256 
1631269680189396528 apache2 munmap < res=0 vm_size=154492 vm_rss=11412 vm_swap=0 
1631269680189403303 apache2 munmap > addr=7F4A8E157000 length=2146944 
1631269680189407837 apache2 munmap < res=0 vm_size=152392 vm_rss=11356 vm_swap=0 
1631269680189419360 apache2 munmap > addr=7F4A8E364000 length=2204928 
1631269680189424593 apache2 munmap < res=0 vm_size=150236 vm_rss=11244 vm_swap=0 
1631269680189435949 apache2 munmap > addr=7F4A8E57F000 length=2385792 
1631269680189443294 apache2 munmap < res=0 vm_size=147904 vm_rss=11148 vm_swap=0 
1631269680189648197 apache2 munmap > addr=7F4A8E7C6000 length=2332344 
1631269680189656863 apache2 munmap < res=0 vm_size=145624 vm_rss=12176 vm_swap=0 
1631269680189697431 apache2 munmap > addr=7F4A97706000 length=151552 
1631269680189705061 apache2 munmap < res=0 vm_size=145476 vm_rss=12068 vm_swap=0 
1631269680189714039 apache2 munmap > addr=7F4A8EA00000 length=2097152 
1631269680189732089 apache2 munmap < res=0 vm_size=143428 vm_rss=10020 vm_swap=0 
1631269680189736218 apache2 munmap > addr=7F4A9772B000 length=323584 
1631269680189738151 apache2 munmap < res=0 vm_size=143112 vm_rss=10016 vm_swap=0 
1631269680189740915 apache2 munmap > addr=7F4A976F0000 length=8192 
1631269680189742760 apache2 munmap < res=0 vm_size=143104 vm_rss=10012 vm_swap=0 
1631269680189742961 apache2 munmap > addr=7F4A976EC000 length=8192 
1631269680189744438 apache2 munmap < res=0 vm_size=143096 vm_rss=10008 vm_swap=0 
1631269680189744593 apache2 munmap > addr=7F4A976EE000 length=8192 
1631269680189745406 apache2 munmap < res=0 vm_size=143088 vm_rss=10004 vm_swap=0 
1631269680189745552 apache2 munmap > addr=7F4A976E8000 length=8192 
1631269680189746735 apache2 munmap < res=0 vm_size=143080 vm_rss=10000 vm_swap=0 
1631269680189746881 apache2 munmap > addr=7F4A976E4000 length=8192 
1631269680189748197 apache2 munmap < res=0 vm_size=143072 vm_rss=9996 vm_swap=0 
1631269680189748346 apache2 munmap > addr=7F4A976EA000 length=8192 
1631269680189749298 apache2 munmap < res=0 vm_size=143064 vm_rss=9988 vm_swap=0 
1631269680189749486 apache2 munmap > addr=7F4A976E6000 length=8192 
1631269680189750794 apache2 munmap < res=0 vm_size=143056 vm_rss=9984 vm_swap=0 
1631269680189753261 apache2 close > fd=5(<p>pipe:[371051716]) 
1631269680189753936 apache2 close < res=0 
1631269680189754148 apache2 close > fd=4(<p>pipe:[371051716]) 
1631269680189754301 apache2 close < res=0 
1631269680189827110 apache2 futex > addr=7F4A9291E8EC op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=2147483647 
1631269680189827650 apache2 futex < res=0 
1631269680189994379 apache2 exit_group >
1631269680190456483 apache2 procexit > status=0 
1631269680203579340 mysqld io_getevents <
1631269680203579789 mysqld io_getevents <
1631269680203581980 mysqld io_getevents >
1631269680203582004 mysqld io_getevents >
1631269680209547423 mysqld io_getevents <
1631269680209548869 mysqld io_getevents >
1631269680261249035 apache2 poll < res=1 fds=10:41 
1631269680261251132 apache2 read > fd=10(<4t>192.168.176.14:43886->192.168.176.15:80) size=8000 
1631269680261253501 apache2 read < res=755 data=UE9TVCAvbG9naW4ucGhwIEhUVFAvMS4xDQpIb3N0OiA0NjUyN2JiOTI0NjAxNmUxDQpDb25uZWN0aW9uOiBrZWVwLWFsaXZlDQpDb250ZW4= 
1631269680261285253 apache2 stat >
1631269680261292806 apache2 stat < res=0 path=/var/www/html/login.php 
1631269680261364069 apache2 brk > addr=5585A22C0000 
1631269680261366476 apache2 brk < res=5585A22C0000 vm_size=374240 vm_rss=10488 vm_swap=0 
1631269680261494080 apache2 brk > addr=5585A22E1000 
1631269680261495172 apache2 brk < res=5585A22E1000 vm_size=374372 vm_rss=11388 vm_swap=0 
1631269680261545226 apache2 setitimer >
1631269680261546603 apache2 setitimer <
1631269680261546938 apache2 rt_sigaction >
1631269680261547286 apache2 rt_sigaction <
1631269680261547702 apache2 rt_sigprocmask >
1631269680261547961 apache2 rt_sigprocmask <
1631269680261608430 apache2 mmap > addr=0 length=65536 prot=3(PROT_READ|PROT_WRITE) flags=10(MAP_PRIVATE|MAP_ANONYMOUS) fd=-1(EPERM) offset=0 
1631269680261610665 apache2 mmap < res=7F4A976D2000 vm_size=374436 vm_rss=12240 vm_swap=0 
1631269680261632725 apache2 getcwd >
1631269680261633533 apache2 getcwd < res=2 path=/ 
1631269680261634166 apache2 chdir >
1631269680261637007 apache2 chdir < res=0 path=/var/www/html 
1631269680261638509 apache2 setitimer >
1631269680261638748 apache2 setitimer <
1631269680261642009 apache2 fcntl > fd=8(<f>/tmp/.ZendSem.5k3hzq (deleted)) cmd=8(F_SETLK) 
1631269680261644739 apache2 fcntl < res=0(<f>/dev/null) 
1631269680261658153 apache2 getcwd >
1631269680261658581 apache2 getcwd < res=14 path=/var/www/html 
1631269680261703619 apache2 open >
1631269680261712003 apache2 open < fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) name=/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63 flags=7(O_CREAT|O_RDWR) mode=0600 dev=1000E0 
1631269680261712820 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) 
1631269680261713925 apache2 fstat < res=0 
1631269680261714574 apache2 getuid >
1631269680261714781 apache2 getuid < uid=33(www-data) 
1631269680261715083 apache2 flock > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) operation=2(LOCK_EX) 
1631269680261716879 apache2 flock < res=0 
1631269680261717098 apache2 fcntl > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) cmd=3(F_SETFD) 
1631269680261717314 apache2 fcntl < res=0(<f>/dev/null) 
1631269680261717510 apache2 fstat > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) 
1631269680261717895 apache2 fstat < res=0 
1631269680261718096 apache2 pread > fd=11(<f>/var/lib/php/sessions/sess_16hh9oarg2onih26f6l4aqll63) size=65 pos=0 
1631269680261721552 apache2 pread < res=65 data=ZHZ3YXxhOjA6e31zZXNzaW9uX3Rva2VufHM6MzI6IjlmYzNjZDExMzI4ZTk3NjUxYTIwZDBhZDY4NzE2MTAwIjs= 
1631269680261738052 apache2 access > mode=0(F_OK) 
1631269680261741915 apache2 access < res=0 name=config/config.inc.php(/var/www/html/config/config.inc.php) 
1631269680261771296 apache2 getcwd >
1631269680261771792 apache2 getcwd < res=14 path=/var/www/html 
1631269680261774788 apache2 lstat >
1631269680261778436 apache2 lstat < res=0 path=/var/www/html/hackable/uploads 
1631269680261778985 apache2 lstat >
1631269680261780379 apache2 lstat < res=0 path=/var/www/html/hackable 
1631269680261780741 apache2 lstat >
1631269680261781886 apache2 lstat < res=0 path=/var/www/html 
1631269680261782161 apache2 lstat >
1631269680261783200 apache2 lstat < res=0 path=/var/www 
1631269680261783660 apache2 lstat >
1631269680261785015 apache2 lstat < res=0 path=/var 
1631269680261790521 apache2 getcwd >
1631269680261790794 apache2 getcwd < res=14 path=/var/www/html 
1631269680261791765 apache2 lstat >
1631269680261795840 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631269680261796419 apache2 lstat >
1631269680261797915 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS/tmp 
1631269680261798400 apache2 lstat >
1631269680261799753 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib/IDS 
1631269680261800183 apache2 lstat >
1631269680261801543 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6/lib 
1631269680261801941 apache2 lstat >
1631269680261803127 apache2 lstat < res=0 path=/var/www/html/external/phpids/0.6 
1631269680261803519 apache2 lstat >
1631269680261804610 apache2 lstat < res=0 path=/var/www/html/external/phpids 
1631269680261804984 apache2 lstat >
1631269680261806018 apache2 lstat < res=0 path=/var/www/html/external 
1631269680261807474 apache2 getcwd >
1631269680261807666 apache2 getcwd < res=14 path=/var/www/html 
1631269680261808166 apache2 lstat >
1631269680261809646 apache2 lstat < res=0 path=/var/www/html/config 
1631269680261821694 apache2 open >
1631269680261826775 apache2 open < fd=12(<f>/etc/passwd) name=/etc/passwd flags=4097(O_RDONLY|O_CLOEXEC) mode=0 dev=1000E0 
1631269680261828156 apache2 lseek > fd=12(<f>/etc/passwd) offset=0 whence=1(SEEK_CUR) 
1631269680261828640 apache2 lseek < res=0 
1631269680261829589 apache2 fstat > fd=12(<f>/etc/passwd) 
1631269680261830141 apache2 fstat < res=0 
1631269680261830443 apache2 mmap > addr=0 length=1022 prot=1(PROT_READ) flags=1(MAP_SHARED) fd=12(<f>/etc/passwd) offset=0 
1631269680261832570 apache2 mmap < res=7F4A97839000 vm_size=374440 vm_rss=13812 vm_swap=0 
1631269680261832753 apache2 lseek > fd=12(<f>/etc/passwd) offset=1022 whence=0(SEEK_SET) 
1631269680261833127 apache2 lseek < res=1022 
1631269680261837573 apache2 munmap > addr=7F4A97839000 length=1022 
1631269680261840002 apache2 munmap < res=0 vm_size=374436 vm_rss=13812 vm_swap=0 
1631269680261840224 apache2 close > fd=12(<f>/etc/passwd) 
1631269680261840668 apache2 close < res=0 
1631269680261844186 apache2 access > mode=2(W_OK) 
1631269680261846672 apache2 access < res=0 name=/var/www/html/hackable/uploads/ 
1631269680261847602 apache2 access > mode=2(W_OK) 
1631269680261848690 apache2 access < res=0 name=/var/www/html/config 
1631269680261849377 apache2 access > mode=2(W_OK) 
1631269680261851215 apache2 access < res=0 name=/var/www/html/external/phpids/0.6/lib/IDS/tmp/phpids_log.txt 
1631269680261885462 apache2 socket > domain=10(AF_INET6) type=2 proto=0 
1631269680261891025 apache2 socket < fd=12(<6>) 
1631269680261892896 apache2 close > fd=12(<6>) 
1631269680261893091 apache2 close < res=0 
1631269680261920899 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631269680261923494 apache2 socket < fd=12(<4>) 
1631269680261923763 apache2 fcntl > fd=12(<4>) cmd=4(F_GETFL) 
1631269680261924017 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680261924140 apache2 fcntl > fd=12(<4>) cmd=5(F_SETFL) 
1631269680261924287 apache2 fcntl < res=0(<f>/dev/null) 
1631269680261924411 apache2 connect > fd=12(<4>) 
1631269680261978182 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:53984->127.0.0.1:3306 
1631269680261979411 apache2 poll > fds=12:435 timeout=60000 
1631269680262002030 apache2 poll < res=1 fds=12:44 
1631269680262002412 apache2 getsockopt >
1631269680262003571 apache2 getsockopt < res=0 fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631269680262004547 apache2 fcntl > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262004695 mysqld poll < res=1 fds=20:41 
1631269680262004832 apache2 fcntl < res=0(<f>/dev/null) 
1631269680262006506 apache2 setsockopt >
1631269680262007309 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680262007553 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631269680262007728 apache2 setsockopt >
1631269680262008020 mysqld fcntl < res=2(<p>pipe:[371051682]) 
1631269680262008358 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262008380 apache2 setsockopt < res=0 fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680262008607 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262008973 mysqld accept >
1631269680262009645 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262033040 mysqld accept < fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) tuple=127.0.0.1:53984->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631269680262033883 mysqld fcntl > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) cmd=2(F_GETFD) 
1631269680262034131 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262034299 mysqld fcntl > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680262034474 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262035033 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262035217 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262035517 mysqld fcntl > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680262035641 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262056555 mysqld fcntl > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262056883 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262057244 mysqld setsockopt >
1631269680262059158 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631269680262059672 mysqld setsockopt >
1631269680262060067 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680262061679 mysqld futex > addr=55B71A4C1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631269680262065476 mysqld futex < res=1 
1631269680262066247 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631269680262068195 mysqld futex < res=0 
1631269680262069764 mysqld futex > addr=55B71A4BEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631269680262070138 mysqld futex < res=0 
1631269680262070773 mysqld gettid >
1631269680262071296 mysqld gettid <
1631269680262073995 mysqld getpeername >
1631269680262075590 mysqld getpeername <
1631269680262081465 mysqld setsockopt >
1631269680262082211 mysqld setsockopt < res=0 fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680262110663 mysqld sendto > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=102 tuple=NULL 
1631269680262124956 apache2 poll < res=1 fds=12:41 
1631269680262125336 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262126318 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631269680262127248 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAtwAAAFBaVn00KW1sAP/3LQIAP6AVAAAAAAAAAAAAAFVIRmRIeEc6KmM2IgA= 
1631269680262128454 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262129148 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680262130010 mysqld poll > fds=41:43 timeout=10000 
1631269680262130426 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262130859 apache2 poll < res=1 fds=12:41 
1631269680262131045 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=102 
1631269680262131881 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC3AAAAUFpWfTQpbWwA//ctAgA/oBUAAAAAAAAAAAAAVUhGZEh4RzoqYzYiAG15c3E= tuple=NULL 
1631269680262158196 apache2 sendto > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=106 tuple=NULL 
1631269680262169195 apache2 sendto < res=106 data=ZgAAAYWiCgAAAADALQAAAAAAAAAAAAAAAAAAAAAAAAAAAAAAYXBwABQz0/36HIgs5qSGw3MolZOa5zhLqwBteXNxbF9uYXRpdmVfcGFzc3c= 
1631269680262169646 mysqld poll < res=1 fds=41:41 
1631269680262170415 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262170504 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262171445 mysqld recvfrom < res=4 data=ZgAAAQ== tuple=NULL 
1631269680262171862 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=102 
1631269680262172701 mysqld recvfrom < res=102 data=haIKAAAAAMAtAAAAAAAAAAAAAAAAAAAAAAAAAAAAAABhcHAAFDPT/fociCzmpIbDcyiVk5rnOEurAG15c3FsX25hdGl2ZV9wYXNzd29yZAA= tuple=NULL 
1631269680262177757 mysqld sendto > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=48 tuple=NULL 
1631269680262186669 mysqld sendto < res=48 data=LAAAAv5teXNxbF9uYXRpdmVfcGFzc3dvcmQAUFpWfTQpbWxVSEZkSHhHOipjNiIA 
1631269680262186695 apache2 poll < res=1 fds=12:41 
1631269680262187006 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262187199 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262187558 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680262187768 apache2 recvfrom < res=4 data=LAAAAg== tuple=NULL 
1631269680262187940 mysqld poll > fds=41:43 timeout=10000 
1631269680262188419 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262188736 apache2 poll < res=1 fds=12:41 
1631269680262188908 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=102 
1631269680262189578 apache2 recvfrom < res=44 data=/m15c3FsX25hdGl2ZV9wYXNzd29yZABQWlZ9NCltbFVIRmRIeEc6KmM2IgA= tuple=NULL 
1631269680262192299 apache2 sendto > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=24 tuple=NULL 
1631269680262199328 apache2 sendto < res=24 data=FAAAAzPT/fociCzmpIbDcyiVk5rnOEur 
1631269680262199984 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262200657 mysqld poll < res=1 fds=41:41 
1631269680262201603 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262202526 mysqld recvfrom < res=4 data=FAAAAw== tuple=NULL 
1631269680262203002 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=20 
1631269680262203784 mysqld recvfrom < res=20 data=M9P9+hyILOakhsNzKJWTmuc4S6s= tuple=NULL 
1631269680262208847 mysqld sendto > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=11 tuple=NULL 
1631269680262216744 apache2 poll < res=1 fds=12:41 
1631269680262216747 mysqld sendto < res=11 data=BwAABAAAAAIAAAA= 
1631269680262217044 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=58 
1631269680262236223 apache2 recvfrom < res=11 data=BwAABAAAAAIAAAA= tuple=NULL 
1631269680262237986 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262238502 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680262238857 mysqld poll > fds=41:43 timeout=28800000 
1631269680262248923 apache2 sendto > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=13 tuple=NULL 
1631269680262256777 apache2 sendto < res=13 data=CQAAAANVU0UgZHZ3YQ== 
1631269680262256820 mysqld poll < res=1 fds=41:41 
1631269680262257217 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262257748 mysqld recvfrom < res=4 data=CQAAAA== tuple=NULL 
1631269680262258147 apache2 poll > fds=12:431 timeout=1471228928 
1631269680262258222 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=9 
1631269680262258703 mysqld recvfrom < res=9 data=A1VTRSBkdndh tuple=NULL 
1631269680262269263 mysqld access > mode=0(F_OK) 
1631269680262275153 mysqld access < res=0 name=./dvwa(/var/lib/mysql/dvwa) 
1631269680262279827 mysqld sendto > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=11 tuple=NULL 
1631269680262307913 apache2 poll < res=1 fds=12:41 
1631269680262308249 apache2 recvfrom > fd=12(<4t>127.0.0.1:53984->127.0.0.1:3306) size=47 
1631269680262308288 mysqld sendto < res=11 data=BwAAAQAAAAIAAAA= 
1631269680262309161 apache2 recvfrom < res=11 data=BwAAAQAAAAIAAAA= tuple=NULL 
1631269680262311829 mysqld recvfrom > fd=41(<4t>127.0.0.1:53984->127.0.0.1:3306) size=4 
1631269680262312281 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
1631269680262312604 mysqld poll > fds=41:43 timeout=28800000 
1631269680262331570 apache2 socket > domain=2(AF_INET) type=1 proto=0 
1631269680262335414 apache2 socket < fd=13(<4>) 
1631269680262335716 apache2 fcntl > fd=13(<4>) cmd=4(F_GETFL) 
1631269680262335957 apache2 fcntl < res=2(<f>/var/log/apache2/error.log) 
1631269680262336074 apache2 fcntl > fd=13(<4>) cmd=5(F_SETFL) 
1631269680262336185 apache2 fcntl < res=0(<f>/dev/null) 
1631269680262336298 apache2 connect > fd=13(<4>) 
1631269680262355762 apache2 connect < res=-115(EINPROGRESS) tuple=127.0.0.1:53986->127.0.0.1:3306 
1631269680262356671 apache2 poll > fds=13:435 timeout=60000 
1631269680262357348 apache2 poll < res=1 fds=13:44 
1631269680262357635 apache2 getsockopt >
1631269680262358182 apache2 getsockopt < res=0 fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) level=1(SOL_SOCKET) optname=4(SO_ERROR) val=0 optlen=4 
1631269680262358535 apache2 fcntl > fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262358751 apache2 fcntl < res=0(<f>/dev/null) 
1631269680262359154 mysqld poll < res=1 fds=20:41 
1631269680262359686 apache2 setsockopt >
1631269680262360132 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680262360294 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=4(F_GETFL) 
1631269680262360438 apache2 setsockopt >
1631269680262360648 mysqld fcntl < res=2(<p>pipe:[371051682]) 
1631269680262360855 apache2 setsockopt < res=0 fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680262360860 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262361053 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262361307 mysqld accept >
1631269680262361492 apache2 poll > fds=13:431 timeout=1471228928 
1631269680262381464 mysqld accept < fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) tuple=127.0.0.1:53986->127.0.0.1:3306 queuepct=0 queuelen=0 queuemax=80 
1631269680262382656 mysqld fcntl > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) cmd=2(F_GETFD) 
1631269680262383083 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262383471 mysqld fcntl > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680262383829 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262384419 mysqld fcntl > fd=20(<4t>127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262384755 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262385170 mysqld fcntl > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) cmd=3(F_SETFD) 
1631269680262385461 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262412255 mysqld fcntl > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) cmd=5(F_SETFL) 
1631269680262412566 mysqld fcntl < res=0(<f>/dev/null) 
1631269680262412825 mysqld setsockopt >
1631269680262413821 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) level=0(UNKNOWN) optname=0(UNKNOWN) val=CAAAAA== optlen=4 
1631269680262414308 mysqld setsockopt >
1631269680262414725 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) level=2(SOL_TCP) optname=0(UNKNOWN) val=AQAAAA== optlen=4 
1631269680262415565 mysqld futex > addr=55B71A4C1364 op=133(FUTEX_PRIVATE_FLAG|FUTEX_WAKE_OP) val=1 
1631269680262418579 mysqld futex < res=1 
1631269680262419194 mysqld poll > fds=20:41 21:u1 timeout=4294967295 
1631269680262421169 mysqld futex < res=0 
1631269680262422514 mysqld futex > addr=55B71A4BEE40 op=129(FUTEX_PRIVATE_FLAG|FUTEX_WAKE) val=1 
1631269680262422895 mysqld futex < res=0 
1631269680262423408 mysqld gettid >
1631269680262423863 mysqld gettid <
1631269680262425770 mysqld getpeername >
1631269680262427189 mysqld getpeername <
1631269680262430846 mysqld setsockopt >
1631269680262431775 mysqld setsockopt < res=0 fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) level=1(SOL_SOCKET) optname=9(SO_KEEPALIVE) val=1 optlen=4 
1631269680262433993 mysqld sendto > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) size=102 tuple=NULL 
1631269680262448056 apache2 poll < res=1 fds=13:41 
1631269680262448391 apache2 recvfrom > fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) size=4 
1631269680262449293 apache2 recvfrom < res=4 data=YgAAAA== tuple=NULL 
1631269680262450032 apache2 poll > fds=13:431 timeout=1471228928 
1631269680262450336 apache2 poll < res=1 fds=13:41 
1631269680262450563 apache2 recvfrom > fd=13(<4t>127.0.0.1:53986->127.0.0.1:3306) size=102 
1631269680262450650 mysqld sendto < res=102 data=YgAAAAo1LjUuNS0xMC4xLjI2LU1hcmlhREItMCtkZWI5dTEAuAAAAFZ5IjYsdzhNAP/3LQIAP6AVAAAAAAAAAAAAAFpeRyo7K2ItWl1GJgA= 
1631269680262451303 apache2 recvfrom < res=98 data=CjUuNS41LTEwLjEuMjYtTWFyaWFEQi0wK2RlYjl1MQC4AAAAVnkiNix3OE0A//ctAgA/oBUAAAAAAAAAAAAAWl5HKjsrYi1aXUYmAG15c3E= tuple=NULL 
1631269680262451588 mysqld recvfrom > fd=74(<4t>127.0.0.1:53986->127.0.0.1:3306) size=4 
1631269680262452237 mysqld recvfrom < res=-11(EAGAIN) data= tuple=NULL 
