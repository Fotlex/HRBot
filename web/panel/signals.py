from django.db import transaction
from django.db.models.signals import post_save
from django.dispatch import receiver

from .models import Mailing, Document, Quiz



@receiver(post_save, sender=Mailing)
def mailing_post_save(sender, instance: Mailing, created, **kwargs):
    from .tasks import send_mailing

    if created:
        transaction.on_commit(lambda: send_mailing.apply_async(args=[instance.id], eta=instance.datetime))


@receiver(post_save, sender=Document)
def document_post_save(sender, instance: Document, created, **kwargs):
    from .tasks import notify_new_document
    if created:
        transaction.on_commit(lambda: notify_new_document.delay(instance.id))


@receiver(post_save, sender=Quiz)
def quiz_post_save(sender, instance: Quiz, created, **kwargs):
    from .tasks import notify_new_quiz
    if created:
        transaction.on_commit(lambda: notify_new_quiz.delay(instance.id))
