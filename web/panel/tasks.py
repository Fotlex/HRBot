import json
import time
from contextlib import ExitStack

import requests
from celery import shared_task

from config import config
from .models import Mailing, User, Document, Quiz, QuizAttempt


@shared_task
def send_mailing(mailing_id: int):
    mailing = Mailing.objects.get(id=mailing_id)

    attachments = mailing.attachments.all()

    users = User.objects.filter(is_active=True)

    if mailing.departments.exists():
        users = users.filter(department__in=mailing.departments.all())
    
    def send_mail(user_id):
        if not attachments:
            requests.post(
                url=f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage',
                json={
                    'chat_id': user_id,
                    'text': mailing.text,
                }
            )
            return

        if len(attachments) == 1:
            attachment = attachments[0]
            attachment_type = attachment.type

            if not attachment.file_id:
                with open(attachment.file.path, 'rb') as f:
                    files = {attachment_type: f}
                    response = requests.post(
                        url=f'https://api.telegram.org/bot{config.BOT_TOKEN}/send{attachment_type.capitalize()}',
                        data={
                            'chat_id': user_id,
                            'caption': mailing.text
                        },
                        files=files
                    )

                    if attachment_type == 'photo':
                        file_id = response.json()['result']['photo'][-1]['file_id']
                    else:
                        print(response.json())
                        file_id = response.json()['result'][attachment_type]['file_id']

                    attachment.file_id = file_id
                    attachment.save()
                    return

            requests.post(
                url=f'https://api.telegram.org/bot{config.BOT_TOKEN}/send{attachment_type.capitalize()}',
                data={
                    'chat_id': user_id,
                    'caption': mailing.text,
                    attachment_type: attachment.file_id,
                }
            )
            return

        with ExitStack() as stack:
            media_group = [
                {
                    'type': attachment.type,
                    'media': f'attach://{attachment.file.name}' if not attachment.file_id else attachment.file_id,
                } for attachment in attachments
            ]

            media_group[0]['caption'] = mailing.text

            files = {}
            for attachment in attachments:
                if not attachment.file_id:
                    file_obj = stack.enter_context(open(attachment.file.path, 'rb'))
                    files[attachment.file.name] = file_obj

            response = requests.post(
                f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMediaGroup',
                data={'chat_id': user_id, 'media': json.dumps(media_group)},
                files=files if files else None
            )

            json_response = response.json()

            for i, attachment in enumerate(attachments):
                if attachment.type == 'photo':
                    attachment.file_id = json_response['result'][i][attachment.type][-1]['file_id']
                else:
                    attachment.file_id = json_response['result'][i][attachment.type]['file_id']
                attachment.save()

    def send_mail_delay(user_id: int):
        send_mail(user_id)
        time.sleep(0.01)

    for user in users:
        send_mail_delay(user.id)

    mailing.is_ok = True
    mailing.save()


def _send_telegram_message(user_id: int, text: str):
    url = f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage'
    payload = {
        'chat_id': user_id,
        'text': text,
    }
    try:
        requests.post(url, json=payload)
    except Exception as e:
        print(f"Error sending message to {user_id}: {e}")
    time.sleep(0.05)


@shared_task
def notify_new_document(document_id: int):
    try:
        doc = Document.objects.get(id=document_id)
        users_to_notify = User.objects.filter(department=doc.department, is_active=True)
        message = f"📚 Появился новый документ: «{doc.title}».\n\nВы можете найти его в разделе «Мои документы»."
        for user in users_to_notify:
            _send_telegram_message(user.id, message)
    except Document.DoesNotExist:
        pass


@shared_task
def notify_new_quiz(quiz_id: int):
    try:
        quiz = Quiz.objects.get(id=quiz_id)
        users_to_notify = User.objects.filter(department=quiz.department, is_active=True)
        message = f"❓ Добавлен новый тест: «{quiz.title}».\n\nПожалуйста, пройдите его в разделе «Квизы»."
        for user in users_to_notify:
            _send_telegram_message(user.id, message)
    except Quiz.DoesNotExist:
        pass
    
    
@shared_task
def send_daily_quiz_reminders():
    users = User.objects.filter(is_active=True, department__isnull=False)

    for user in users:
        department_quizzes = Quiz.objects.filter(department=user.department)
        
        completed_quiz_ids = QuizAttempt.objects.filter(user=user).values_list('quiz_id', flat=True)
        
        pending_quizzes = department_quizzes.exclude(id__in=completed_quiz_ids)
        
        count = pending_quizzes.count()
        
        if count > 0:
            text = (
                f"🔔 <b>Напоминание</b>\n\n"
                f"У вас есть непройденные тесты ({count} шт.).\n"
                f"Пожалуйста, зайдите в раздел «Квизы» и пройдите их."
            )
            try:
                requests.post(
                    f'https://api.telegram.org/bot{config.BOT_TOKEN}/sendMessage',
                    json={
                        'chat_id': user.id,
                        'text': text,
                        'parse_mode': 'HTML'
                    }
                )
                time.sleep(0.05)
            except Exception as e:
                print(f"Error sending reminder to {user.id}: {e}")

