## Домашнее задание №2

### Запуск
Из папки hw1 применить команду

`kubectl apply -f . && kubectl apply -f ./secrets -n hw2  && kubectl apply -f ./entities -n hw2`

Для проверки url выполнить команду:

`curl  http://arch.homework/health && curl http://arch.homework/otusapp/sergey/volkov`

### Задание 
Создать минимальный сервис, который:
отвечает на порту 8000
имеет http-метод GET /health/ RESPONSE: {"status": "OK"}
Cобрать локально образ приложения в докер.
Запушить образ в dockerhub

Написать манифесты для деплоя в k8s для этого сервиса.

Манифесты должны описывать сущности Deployment, Service, Ingress.
В Deployment могут быть указаны Liveness, Readiness пробы.
Количество реплик должно быть не меньше 2. Image контейнера должен быть указан с Dockerhub.

Хост в ингрессе должен быть arch.homework. В итоге после применения манифестов GET запрос на http://arch.homework/health должен отдавать {“status”: “OK”}.

На выходе предоставить
0) ссылку на github c манифестами. Манифесты должны лежать в одной директории, так чтобы можно было их все применить одной командой kubectl apply -f .

url, по которому можно будет получить ответ от сервиса (либо тест в postmanе).
Задание со звездой* (+5 баллов):
В Ingress-е должно быть правило, которое форвардит все запросы с /otusapp/{student name}/* на сервис с rewrite-ом пути. Где {student name} - это имя студента.

### Неисправности
Если не работает, проверить что в `etc/hosts` прописан адрес из команды `minikube ip`

`192.168.49.2 arch.homework`

Проверить что в minikube есть ingress:
`minikube addons enable ingress`