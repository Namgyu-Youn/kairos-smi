# 1. 작동 원리
1. SSH 접속에는 2가지 정보가 필요하다. : "host"@"ip":"port", RSA key(public/private)
2. 특정 local에서 다수의 SSH 서버들을 모두 접속해 GPU를 독점하는 것도 가능함. (모든 SSH 서버들에 접속된 local을 Head라고 부르겠습니다.)
3. Head가 모든 SSH 서버들을 동시에 접속한다면, 일종의 Cluster 형태가 됨
4. Head가 아닌 local에서 SSH 접속 : Head에서 **공유 키**를 받아서 접속함


# 2. 예상되는 장단점
1. Pros (장점)
- SSH(GPU) 자동 분배가 가능해진다. (공유 키로 접속하면 비어있는 GPU로 자동 할당됨)
- Head에서 모든 서버의 gpu 사용량을 모니터링할 수 있음.

2. Cons (단점)
- Latency(지연)의 가능성 있음.
- 저장소 동기화 문제 : 접속할 때마다 다른 서버를 할당받을 수 있어서, 저장소 동기화 문제가 발생한다.
- 한 서버가 터진다면, 모든 서버가 함께 폭파할(!) 가능성 존재함.
![[Pasted image 20241015023116.png | 500]] 

# 3. Read more
- [kairos-smi Github](https://github.com/kairos03/kairos-smi) : 해당 Open source를 fork해서 주석을 추가했습니다.
- [LINK](https://davi06000.tistory.com/165) : 단일 local에서 멀티 노드를 통한 분산 컴퓨팅에 관한 자료입니다.
- [Tistory](https://skk095.tistory.com/30) : Pycharm 환경에서 SSH Clustering입니다.
- [Ray with GCP](https://speakerdeck.com/mlopskr/ray-daegyumo-mlinpeurareul-wihan-bunsan-siseutem-peureimweokeu-josangbin) : 대규모 frame-work에서 Cloud를 활용해 분산 컴퓨팅을 하는 내용을 소개합니다.
