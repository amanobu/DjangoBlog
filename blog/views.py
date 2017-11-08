# -*- coding: utf-8 -*- 
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from blog.models import Post, Comment
from django.utils import timezone
from blog.forms import PostForm, CommentForm

from django.views.generic import (TemplateView,ListView,
                                  DetailView,CreateView,
                                  UpdateView,DeleteView)

from django.urls import reverse_lazy
from django.contrib.auth.mixins import LoginRequiredMixin

class AboutView(TemplateView):
    template_name = 'about.html'

class PostListView(ListView):
    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__lte=timezone.now()).order_by('-published_date')

    #templateの指定はしていないが、勝手に<app name>/<model name>_list.htmlになる模様
    #なのでこの場合はblog/post_list.html

class PostDetailView(DetailView):
    model = Post

    #templateの指定はしていないが、勝手に<app name>/<model name>_detail.htmlになる模様
    #なのでこの場合はblog/post_detail.html


#ClassベースのViewを使う場合はLoginRequiredMixin
#継承する際に一番←に無ければならない！！！
class CreatePostView(LoginRequiredMixin,CreateView):
    #以下の２パラメータを設定しなければ、raise_exceptionでハンドリング。何もしないと403で返却される
    login_url = '/login/'
    redirect_field_name = 'blog/post_detail.html'

    #対応するformクラスの設定
    form_class = PostForm

    #対応するmodelの設定
    model = Post


class PostUpdateView(LoginRequiredMixin,UpdateView):
    login_url = '/login/'
    redirect_field_name = 'blog/post_detail.html'

    form_class = PostForm

    model = Post


class DraftListView(LoginRequiredMixin,ListView):
    login_url = '/login/'
    redirect_field_name = 'blog/post_list.html'

    model = Post

    def get_queryset(self):
        return Post.objects.filter(published_date__isnull=True).order_by('created_date')


class PostDeleteView(LoginRequiredMixin,DeleteView):
    model = Post
    #django.urls.reverse_lazyを使う際はドキュメントによると
    #class-based viewを使っているとき
    #デコレータによりpermission_required等をしているとき
    #三つめの例は良く分からない...
    success_url = reverse_lazy('post_list')

#######################################
## Functions that require a pk match ##
#######################################

#@login_requireについて
#ユーザがログインしていなければ、settings.LOGIN_URLにリダイレクトし、クエリ文字列に現在の絶対パスを渡す
#デフォルトでは、認証に成功したユーザがリダイレクトされる先のパスは "next" という名称のクエリパラメータに格納。
#もし異なるパラメータ名を利用したい場合、login_required() が redirect_field_name という省略可能な引数を受け取ります:
#@login_required(redirect_field_name='my_redirect_field')
#こうするとnextを使わず、redirect_field_nameが使われる
@login_required
def post_publish(request, pk):
    #get_object_or_404(klass, *args, **kwargs)
    #klass:Modelだったり、Manager(?)だったり、QuerySet(?)だったりを渡す
    #検索パラメータ。title__startswith='M'とか。,で区切るとand条件になる
    post = get_object_or_404(Post, pk=pk)
    post.publish()
    return redirect('post_detail', pk=pk)

@login_required
def add_comment_to_post(request, pk):
    #まず、親となる記事postのデータを取ってきて、
    post = get_object_or_404(Post, pk=pk)
    if request.method == "POST":
        #バリデーションの為一旦Formを得る？
        form = CommentForm(request.POST)
        if form.is_valid():
            #で、チェックが問題無ければcommentを保存する前にcommentのインスタンスをgetして
            comment = form.save(commit=False)
            #親のpostをひも付けて
            comment.post = post
            #書き込み
            comment.save()
            return redirect('post_detail', pk=post.pk)
    else:
        #post以外はformを見せるみたいだな
        form = CommentForm()
    return render(request, 'blog/comment_form.html', {'form': form})


@login_required
def comment_approve(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    #コメントの承認をして保存する
    comment.approve()
    return redirect('post_detail', pk=comment.post.pk)


@login_required
def comment_remove(request, pk):
    comment = get_object_or_404(Comment, pk=pk)
    post_pk = comment.post.pk
    comment.delete()
    return redirect('post_detail', pk=post_pk)

'''
Viewについて：https://docs.djangoproject.com/en/1.11/ref/class-based-views/
・ClassベースのViewを使う場合、リクエスト毎に独立した状態を持っている様なのでThreadSafeだ
・Viewに渡される引数(initializerの事かな？)は共有されるとさ
・各クラス毎に処理フローがあり、それは必ず確認した方がよさそう(MROの事(Method Resolution Order))
・templatenameは<app_label>/<model_name><template_name_suffix>.html
・細かい事はこの辺のソースを見るのが良さそうだ：https://github.com/django/django/tree/master/django/views/generic
・DeleteViewはGetで呼ばれると確認画面を表示するView(template:～_confirm_delete.html)となり、POSTで呼ばれると削除される

'''
