# Операции со стендом

Команды Ansible запускаются на управляющем компьютере из корня репозитория.
`inventory/server.yml` — локальная копия примера с вашими параметрами, вне Git.
Для административных операций используйте проверенное sudo/root-подключение.

## Повторное применение

```bash
source .venv/bin/activate
ansible-playbook -i inventory/server.yml playbooks/deploy.yml
```

Меняется шаблон на управляющем компьютере, затем Ansible доставляет результат
на сервер. Обновление окружения или подключений контейнера требует применения
Compose с выбранным сервисом; простой restart не обновляет его конфигурацию.

## Диагностика на сервере

```bash
docker compose -f /opt/nextcloud-lab/stack/compose.yml ps
docker compose -f /opt/nextcloud-lab/stack/compose.yml logs --tail=50 nginx
docker compose -f /opt/nextcloud-lab/stack/compose.yml exec -T --user www-data nextcloud php occ status
docker compose -f /opt/nextcloud-lab/stack/compose.yml exec -T --user www-data nextcloud php occ onlyoffice:documentserver --check
```

Если изменён `project_dir`, замените путь. Не публикуйте журнал без просмотра:
он может содержать токены, имена пользователей и адреса.

## Отключение пользователя

Сначала определите и проверьте соответствие пользователя authentik и UID Nextcloud.
Идентификатор OIDC может быть хешем, а не именем входа.

```bash
ansible-playbook -i inventory/server.yml playbooks/disable-user.yml \
  -e disabled_authentik_user=labuser \
  -e disabled_nextcloud_uid=REPLACE_WITH_VERIFIED_NEXTCLOUD_UID \
  -e disabled_expected_display_name=labuser
```

Операция деактивирует пользователя в authentik и отзывает токены Nextcloud,
включая пароли приложений. Данные и учётная запись не удаляются. Сопоставление
двух учётных записей пока задаёт оператор; отображаемое имя — дополнительная
проверка от ошибки, а не криптографическая привязка.

Для восстановления включите пользователя в authentik и выполните новый вход.
Отозванные пароли приложений потребуется создать заново. Этот плейбук намеренно
не включён в deploy.

## Проверка продления сертификатов на сервере

```bash
/opt/nextcloud-lab/stack/scripts/renew-certificates.sh --dry-run --run-deploy-hooks
systemctl list-timers --all --no-pager nextcloud-cert-renew.timer
```

Dry run использует тестовый ACME-сервер. Запросы выполняются по очереди;
Certbot может выдерживать случайную задержку. Проверяется также hook reload nginx.

## Что не автоматизировано

Первая установка Docker, регистрация первого ACME-аккаунта, доставка собственных
образов на чистый сервер, SSH-hardening, Vault, backup/restore и обновление с
откатом. Не запускайте destructive volume/prune-команды как часть обычного deploy.
