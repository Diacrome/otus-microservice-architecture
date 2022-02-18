## Домашнее задание №2

### Запуск
Проверить что в minikube есть ingress:

`minikube addons enable ingress`

Из папки hw5 применить команду

```
kubectl apply -f . &&
kubectl apply -f ./secrets -n bondiana &&
helm repo add bitnami https://charts.bitnami.com/bitnami &&
helm install service bitnami/postgresql -n bondiana -f ./helm/values.yaml &&
kubectl apply -f ./config -n bondiana &&
kubectl apply -f ./python_app -n bondiana
```

Для проверки CRUD выполнить команду:

`newman run ./test/bondiana.postman_collection.json`

### Задание 



### Код
В папке `python_docker_code` исходный код приложения

### Неисправности
Если не работает, проверить что в `etc/hosts` прописан адрес из команды `minikube ip`

`192.168.49.2 arch.homework`

Проверить что в minikube есть ingress:
`minikube addons enable ingress`