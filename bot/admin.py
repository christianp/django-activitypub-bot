from django import forms
from django.contrib import admin
from django.template.response import TemplateResponse
from django.urls import path
from django.views import generic
from .models import LocalActor, Note

# Register your models here.
class LocalActorAdmin(admin.ModelAdmin):
    change_form_template = "admin/localactor_change_form.html"
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('<int:pk>/create_note/', self.admin_site.admin_view(CreateNoteView.as_view()), name='admin_create_note'),
                path('<int:pk>/mentions/', self.admin_site.admin_view(MentionsView.as_view()), name='admin_mentions'),
        ]
        return my_urls + urls

    def create_note_view(self, request, pk):
        actor = LocalActor.objects.get(pk=pk)
        context = dict(
           self.admin_site.each_context(request),
           actor = actor,
        )
        return TemplateResponse(request, "admin/create_note.html", context)

class CreateNoteForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Note
        fields = ['local_actor']

    def save(self, commit=True):
        content = self.cleaned_data['content']
        local_actor = self.cleaned_data['local_actor']
        return local_actor.create_note(content)

class CreateNoteView(generic.CreateView):
    model = Note
    form_class = CreateNoteForm
    template_name = 'admin/create_note.html'
    
    def get_initial(self):
        initial = super().get_initial()
        initial['local_actor'] = LocalActor.objects.get(pk=self.kwargs.get('pk'))
        return initial

class UpdateNoteForm(forms.ModelForm):
    content = forms.CharField(widget=forms.Textarea)
    class Meta:
        model = Note
        fields = []

    def save(self, commit=True):
        note = super().save(commit=False)
        content = self.cleaned_data['content']
        note.data['content'] = content
        note.data = Note.filter_data(note.data)

        if commit:
            note.save()

        return note

class UpdateNoteView(generic.UpdateView):
    model = Note
    form_class = UpdateNoteForm
    template_name = 'admin/update_note.html'

    def get_initial(self):
        initial = super().get_initial()
        initial['content'] = self.object.data.get('content','')
        return initial

class MentionsView(generic.DetailView):
    model = LocalActor
    template_name = 'admin/mentions.html'

admin.site.register(LocalActor, LocalActorAdmin)

class NoteAdmin(admin.ModelAdmin):
    change_form_template = "admin/note_change_form.html"
    def get_urls(self):
        urls = super().get_urls()
        my_urls = [
                path('<uuid:pk>/update/', self.admin_site.admin_view(UpdateNoteView.as_view()), name='admin_update_note'),
        ]
        return my_urls + urls
admin.site.register(Note, NoteAdmin)
