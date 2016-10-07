from django import forms
from elec9606.settings import MAX_IMAGE_SIZE, MAX_MUSIC_SIZE


IS_PRIVATE = [
    (True, True),
    (False, False)
]

MUSIC_TYPE = [
    'mp3'
]


class LoginForm(forms.Form):
    username = forms.CharField(max_length=150)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)


class RegisterForm(forms.Form):
    username = forms.CharField(max_length=150)
    firstname = forms.CharField(max_length=30)
    lastname = forms.CharField(max_length=30)
    email = forms.EmailField(max_length=254)
    password = forms.CharField(max_length=32, widget=forms.PasswordInput)


class ImageUploadForm(forms.Form):
    profile = forms.ImageField()

    def clean_file(self):
        file = self.cleaned_data['profile']
        if file._size > MAX_IMAGE_SIZE:
            return False
        else:
            return True


class MusicUploadForm(forms.Form):
    music = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data['music']

        file_type = file.content_type.spilt('.')[1]

        if file_type in MUSIC_TYPE:
            if file._size > MAX_MUSIC_SIZE:
                return False
            else:
                return True
        else:
            return False


class BlogForm(forms.Form):
    title = forms.CharField(max_length=100)
    content = forms.CharField(widget=forms.Textarea)
    private = forms.ChoiceField(choices=IS_PRIVATE)
    music = forms.FileField()

    def clean_file(self):
        file = self.cleaned_data['music']
        info = file.content_type.split('/')
        file_type = info[1]

        if file_type in MUSIC_TYPE:
            if file._size > MAX_MUSIC_SIZE:
                return False
            else:
                return True
        else:
            return False


class ForwardForm(forms.Form):
    fwdcontent = forms.CharField(max_length=100)
    fwdprivate = forms.CharField()


class CommentForm(forms.Form):
    author_id = forms.CharField()
    content = forms.CharField(widget=forms.Textarea)

