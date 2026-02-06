from django.contrib import admin
from django.http import HttpResponseRedirect
from django.urls import reverse
from .models import *
from nested_admin import NestedStackedInline, NestedModelAdmin

@admin.register(Department)
class DepartmentAdmin(admin.ModelAdmin):
    list_display = ('name',)
    search_fields = ('name',)


class CommentInline(admin.TabularInline):
    model = Comment
    
    fields = ('comment',) 
    
    extra = 1 


@admin.register(User)
class UserAdmin(admin.ModelAdmin):
    list_display = ('username', 'full_name', 'department', 'quiz_stats', 'is_active', 'created_at')
    list_filter = ('department', 'is_active')
    
    inlines = [CommentInline]
    
    search_fields = ('username', 'first_name', 'last_name')
    readonly_fields = ('id', 'username', 'first_name', 'last_name', 'created_at')
    fieldsets = (
        ('Управление доступом', {
            'fields': ('department', 'is_active')
        }),
        ('Инфо', {
            'fields': ('id', 'username', 'first_name', 'last_name', 'created_at')
        }),
    )

    @admin.display(description='Имя')
    def full_name(self, obj):
        return f"{obj.first_name or ''} {obj.last_name or ''}".strip() or obj.username

    @admin.display(description='Пройдено квизов')
    def quiz_stats(self, obj):
        if not obj.department:
            return "-"
        total = Quiz.objects.filter(department=obj.department).count()
        passed = QuizAttempt.objects.filter(user=obj).values('quiz').distinct().count()
        
        return f"{passed} из {total}"
    
    class Media:
        js = ('js/admin_popup_fix.js',)


@admin.register(Document)
class DocumentAdmin(admin.ModelAdmin):
    list_display = ('title', 'display_departments', 'created_at')
    list_filter = ('department',)
    search_fields = ('title',)
    
    filter_horizontal = ('department',) 

    @admin.display(description='Подразделения')
    def display_departments(self, obj):
        return ", ".join([d.name for d in obj.department.all()])
    
    class Media:
        js = ('js/admin_popup_fix.js',)


class AnswerNestedInline(NestedStackedInline):
    model = Answer
    extra = 1
    fk_name = 'question'

class QuestionNestedInline(NestedStackedInline):
    model = Question
    extra = 1
    inlines = [AnswerNestedInline]
    fk_name = 'quiz'

@admin.register(Quiz)
class QuizAdmin(NestedModelAdmin):
    list_display = ('title', 'document', 'department')
    list_filter = ('department',)
    search_fields = ('title',)
    inlines = [QuestionNestedInline]
    
    class Media:
        js = ('js/admin_popup_fix.js',)

class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 1


class UserAnswerInline(admin.TabularInline):
    model = UserAnswer
    extra = 0
    readonly_fields = ('question_text', 'user_answer_text', 'is_correct_display')
    fields = ('question_text', 'user_answer_text', 'is_correct_display')
    can_delete = False

    def has_add_permission(self, request, obj=None):
        return False

    def get_queryset(self, request):
        return super().get_queryset(request).select_related('question', 'answer')

    @admin.display(description='Текст вопроса')
    def question_text(self, obj):
        return obj.question.text

    @admin.display(description='Ответ пользователя')
    def user_answer_text(self, obj):
        return obj.answer.text

    @admin.display(description='Результат', boolean=True)
    def is_correct_display(self, obj):
        return obj.answer.is_correct

@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = ('user', 'quiz', 'score', 'total_questions_count', 'completed_at')
    list_filter = ('quiz__department', 'quiz')
    readonly_fields = ('user', 'quiz', 'score', 'completed_at')
    inlines = [UserAnswerInline]

    def has_add_permission(self, request):
        return False
    
    class Media:
        js = ('js/admin_popup_fix.js',)
        

class AttachmentsInline(admin.TabularInline):
    model = Attachments
    exclude = ('file_id',)
    extra = 0

@admin.register(Mailing)
class MailingAdmin(admin.ModelAdmin):
    list_display = ['datetime', 'short_text', 'departments_list', 'is_ok']
    readonly_fields = ['is_ok']
    inlines = [AttachmentsInline]
    
    filter_horizontal = ('departments',)
    
    fieldsets = (
        ('Настройки отправки', {
            'fields': ('departments', 'datetime', 'is_ok')
        }),
        ('Содержание', {
            'fields': ('text',)
        }),
    )

    @admin.display(description='Текст')
    def short_text(self, obj):
        return obj.text[:50] + '...' if obj.text and len(obj.text) > 50 else obj.text

    @admin.display(description='Получатели')
    def departments_list(self, obj):
        deps = obj.departments.all()
        if not deps:
            return "📢 ВСЕМ"
        return ", ".join([d.name for d in deps])
    
    class Media:
        js = ('js/admin_popup_fix.js',)
    
    
@admin.register(AboutSection)
class AboutSectionAdmin(admin.ModelAdmin):
    list_display = ('title', 'order')
    list_editable = ('order',)
    
    class Media:
        js = ('js/admin_popup_fix.js',)
    
    
@admin.register(HelpButton)
class HelpButtonAdmin(admin.ModelAdmin):
    pass


class SingletonModelAdmin(admin.ModelAdmin):
    def changelist_view(self, request, extra_context=None):
        obj, _ = self.model.objects.get_or_create(pk=1)
        return HttpResponseRedirect(
            reverse(
                f"admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change",
                args=(obj.pk,),
            )
        )

    def has_add_permission(self, request):
        return False

    def has_delete_permission(self, request, obj=None):
        return False
    
    
@admin.register(HelpPart)
class HelpPartAdmin(SingletonModelAdmin):
    pass