from django.db import models

class Department(models.Model):
    name = models.CharField('Название подразделения', max_length=255, unique=True)

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = 'Подразделение'
        verbose_name_plural = 'Подразделения'


class User(models.Model):
    id = models.BigIntegerField('Идентификатор Телеграм', primary_key=True)
    username = models.CharField('Юзернейм', max_length=64, null=True, blank=True)
    first_name = models.CharField('Имя', null=True, blank=True)
    last_name = models.CharField('Фамилия', null=True, blank=True)
    created_at = models.DateTimeField('Дата регистрации', auto_now_add=True)

    department = models.ForeignKey(
        Department,
        on_delete=models.SET_NULL,
        null=True, blank=True,
        verbose_name='Подразделение',
        related_name='users'
    )
    is_active = models.BooleanField('Активен', default=False)

    def __str__(self):
        return f'@{self.username or self.id}'

    class Meta:
        verbose_name = 'Сотрудник'
        verbose_name_plural = 'Сотрудники'


class Comment(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Пользователь')
    comment = models.TextField(verbose_name='Содержание коментария')
    
    def __str__(self):
        return 'Коментарий'
    
    class Meta:
        verbose_name = 'Коментарий'
        verbose_name_plural = 'Коментарии'


class Document(models.Model):
    title = models.CharField('Название документа', max_length=255)
    description = models.TextField('Описание', null=True, blank=True)
    file = models.FileField('Файл', upload_to='documents/')
    department = models.ManyToManyField(
        Department,
        verbose_name='Подразделения',
        related_name='documents'
    )
    created_at = models.DateTimeField('Дата загрузки', auto_now_add=True)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Документ'
        verbose_name_plural = 'Документы'


class Quiz(models.Model):
    title = models.CharField('Название квиза', max_length=255)
    document = models.ForeignKey(Document, on_delete=models.CASCADE, verbose_name='Документ', related_name='quiz')
    department = models.ForeignKey(Department, on_delete=models.CASCADE, verbose_name='Подразделение', related_name='quizzes')
    send_delay_hours = models.PositiveIntegerField('Задержка отправки (часы)', default=0, editable=False)

    def __str__(self):
        return self.title

    class Meta:
        verbose_name = 'Квиз'
        verbose_name_plural = 'Квизы'


class Question(models.Model):
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name='Квиз', related_name='questions')
    text = models.TextField('Текст вопроса')

    def __str__(self):
        return self.text[:50] + '...'

    class Meta:
        verbose_name = 'Вопрос'
        verbose_name_plural = 'Вопросы'


class Answer(models.Model):
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос', related_name='answers')
    text = models.CharField('Текст ответа', max_length=255)
    is_correct = models.BooleanField('Правильный ответ', default=False)

    def __str__(self):
        return self.text

    class Meta:
        verbose_name = 'Ответ'
        verbose_name_plural = 'Ответы'


class QuizAttempt(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, verbose_name='Сотрудник', related_name='attempts')
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, verbose_name='Квиз', related_name='attempts')
    completed_at = models.DateTimeField('Дата завершения', auto_now_add=True)
    score = models.PositiveIntegerField('Результат (правильных ответов)')

    @property
    def total_questions_count(self):
        return self.quiz.questions.count()
        
    total_questions_count.fget.short_description = 'Всего вопросов'
    
    def __str__(self):
        return f'Попытка {self.user} в квизе {self.quiz.title}'

    class Meta:
        verbose_name = 'Результат квиза'
        verbose_name_plural = 'Результаты квизов'
        unique_together = ('user', 'quiz')


class UserAnswer(models.Model):
    attempt = models.ForeignKey(QuizAttempt, on_delete=models.CASCADE, verbose_name='Попытка', related_name='user_answers')
    question = models.ForeignKey(Question, on_delete=models.CASCADE, verbose_name='Вопрос')
    answer = models.ForeignKey(Answer, on_delete=models.CASCADE, verbose_name='Выбранный ответ')

    def __str__(self):
        return f"Ответ на '{self.question.text[:30]}...'"
        
    class Meta:
        verbose_name = 'Ответ пользователя'
        verbose_name_plural = 'Ответы пользователей'


class Mailing(models.Model):
    departments = models.ManyToManyField(
        Department,
        verbose_name='Подразделения',
        blank=True,
        help_text='Выберите подразделения. Если ничего не выбрано — рассылка уйдет ВСЕМ активным сотрудникам.'
    )
    
    text = models.TextField('Текст', blank=True, null=True)
    datetime = models.DateTimeField('Дата/Время')
    is_ok = models.BooleanField('Статус отправки', default=False)

    class Meta:
        verbose_name = 'Рассылка'
        verbose_name_plural = 'Рассылки'
        ordering = ['-datetime']
        
    def __str__(self):
        dest = "ВСЕМ"
        if self.pk and self.departments.exists():
            dest = f"{self.departments.count()} отд."
        return f"Рассылка {self.datetime} ({dest})"


class Attachments(models.Model):
    types = {
        'photo': 'Фото',
        'video': 'Видео',
        'document': 'Документ'
    }
    type = models.CharField('Тип вложения', choices=types)
    file = models.FileField('Файл', upload_to='web/media/mailing')
    file_id = models.TextField(null=True)
    mailing = models.ForeignKey('Mailing', on_delete=models.SET_NULL, null=True, related_name='attachments')

    class Meta:
        verbose_name = 'Вложение'
        verbose_name_plural = 'Вложения'
        
        
class AboutSection(models.Model):
    title = models.CharField('Заголовок раздела', max_length=255)
    text = models.TextField('Текст')
    order = models.PositiveIntegerField('Порядок отображения', default=0)

    class Meta:
        verbose_name = 'Раздел "О компании"'
        verbose_name_plural = 'Разделы "О компании"'
        ordering = ['order']

    def __str__(self):
        return self.title
    
    
class HelpPart(models.Model):
    text_on_message = models.TextField('Текст на сообщении с кнопками')
    
    class Meta:
        verbose_name = 'Главный текст "Помощь"'
        verbose_name_plural = 'Главный текст "Помощь"'

    def __str__(self):
        return 'Текст в разделе "Помощь"'
    
    
class HelpButton(models.Model):
    text_on_btn = models.CharField(max_length=30, verbose_name='Текст на кнопке')
    url = models.CharField(max_length=255, verbose_name='Ссылка в кнопке')
    
    is_active = models.BooleanField(default=True, verbose_name='Активна ли кнопка')
    
    class Meta:
        verbose_name = 'Кнопки "Помощь"'
        verbose_name_plural = 'Кнопка "Помощь"'

    def __str__(self):
        return f'Кнопка {self.text_on_btn}'