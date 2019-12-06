��    !      $              ,  �   -  �   �     I    W  �   d  D   �  /   .     ^  �   m  �   �     �  L   �  (   �       P   *  {   {  �   �    �  3   �	     �	     �	  
   �	  {   �	  U   a
  �   �
  .   a  �   �  G   5  �   }  �   n  �      K   �  �  �  �   �  �   �     �  �  �  �   s  �   %  `   �  '     �   >  �   1  .     �   I  +   �  0   "  �   S  [   �  �   5  �    J   �       !        6  �   P  �   �    �  k   �  �   �  i   �   �  b!  �   '#  +  $$  n   P%   :attr:`context` here is the object of the :class:`Context` class , which is automatically put into every command's first argument, so be aware of it. :class:`Context` has all the information you need to process the command You can find more information in the Context class reference A Minimal Bot A callback is essentially a function that is called when something happens. In our case, the :func:`on_ready` event is called when the bot has finished logging in and setting things up and the :func:`on_message_new` event is called when the bot has received a message. Afterwards, we check if the :class:`Message.text` starts with ``'$hello'``. If it is, then we reply to the sender with ``'Hello!'``. As you can see, this is a slightly modified version of previous bot. Commands can also take arguments, as shown here Commands usage Finally, we run the bot with our login token. If you need help getting your token or creating a bot, look in the :ref:`vk-intro` section. If you want to get all of the text user sent after certain argument (or even after the command call), you can set up arguments like this It looks something like this: Let's make a bot that replies to a specific message and walk you through it. Let's name this file ``example_bot.py``. Look at this example: Next, we create an instance of a :class:`Bot`. This bot is our connection to VK. Now bot will put everything after the command call into :attr:`name` variable so now you can greet someone with longer name Now that we've made a bot, we have to *run* the bot. Luckily, this is simple since this is just a Python script, we can run it directly. Now user can call command like ``!greet Santa`` and the bot will reply with ``Greetings, Santa``. Arguments taken are positional, and separated with space by default, so if user will call ``!greet Santa Claus`` bot will still reply with just ``Greetings, Santa``. Now you can try playing around with your basic bot. On Windows: On other systems: Quickstart So, for example, let's say your prefix of choice was ``'!'``. It can really be anything, but we will talk about that later. So, now when user sends ``!greet`` to the bot, the bot will reply with ``Greetings!`` The commands are automatically processed messages. You may have noticed that we used a prefix when creating our bot, and the commands are what this prefix is needed for. The difference is the :func:`bot.command` part The first line just imports the library, if this raises a `ModuleNotFoundError` or `ImportError` then head on over to :ref:`installing` section to properly install. There's a lot going on here, so let's walk you through it step by step. They are created using :func:`Bot.command` decorator, that can take several arguments, for example :attr:`name` we used here. By default it will be function name, so we didn't really need it here, but it is just more human-readable this way This page gives a brief introduction to the library. It assumes you have the library installed, if you don't check the :ref:`installing` portion. We then use the :meth:`Bot.listen()` decorator to register an event. This library has many events. Since this library is asynchronous, we do things in a "callback" style manner. vk-botting package has a lot of possibilities for creating commands easily. Project-Id-Version: vk-botting 
Report-Msgid-Bugs-To: 
POT-Creation-Date: 2019-12-07 00:01+0300
PO-Revision-Date: YEAR-MO-DA HO:MI+ZONE
Last-Translator: FULL NAME <EMAIL@ADDRESS>
Language: ru
Language-Team: ru <LL@li.org>
Plural-Forms: nplurals=3; plural=(n%10==1 && n%100!=11 ? 0 : n%10>=2 && n%10<=4 && (n%100<10 || n%100>=20) ? 1 : 2)
MIME-Version: 1.0
Content-Type: text/plain; charset=utf-8
Content-Transfer-Encoding: 8bit
Generated-By: Babel 2.7.0
 :attr:`context` тут - экземпляр класса :class:`Context` , который автоматически передается как первый аргумент к каждой команде, так что будьте на чеку. :class:`Context` содержит всю информацию, необходимую для обработки сообщения. Больше можно найти в отделенном ему разделе в описании классов Простейший бот Функция обратного вызова, по сути, это функция, которая вызывается, когда что-то происходит. В нашем случае, событие :func:`on_ready` вызывается когда бот закончил входить и настраивать все, а :func:`on_message_new` - когда бот получает сообщение. После мы проверяем, начинается ли :class:`Message.text` с ``'$hello'``. Если да, то мы отправляем ответное ``'Hello!'``. Как вы, наверное, заметили, это просто слегка модифицированный предыдущий бот. Команды могут принимать аргументы, как показано тут: Использование команд Наконец, мы запускаем бота с ключом доступа. Если у вас сложности с созданием бота или получением ключа доступа, посмотрите :ref:`vk-intro`. Если необходимо получить в один аргумент весь текст после определенного аргумента (или даже весь вообще), то можно сделать так: Выглядит он примерно так: Давайте сделаем бота, который отвечает на конкретное сообщение, и посмотрим, как все работает. Назовем файл ``example_bot.py``. Посмотрите на этот пример: Дальше, мы создаем экземпляр класса :class:`Bot`. Этот бот и связывает нас с ВК. Теперь бот запишет весь полученный текст в :attr:`name` Теперь, когда мы сделали бота, его надо *запустить*. Но все просто. Так как это просто скрипт на Python, его можно запустить напрямую. Теперь пользователь может вызывать команду как ``!greet Santa``, а бот ответит ``Greetings, Santa``. Принимаемые аргументы позиционны и разделяются пробелами, так что если пользователь вызовет ``!greet Santa Claus`` бот все равно ответит ``Greetings, Santa``. А теперь можете попробовать нового бота. Для Windows: Для других систем: Быстрый старт Предположим, что вы выбрали ``'!'`` как префикс. Он может быть любым, но об этом позже. Тогда теперь, когда пользователь отправляет ``!greet`` боту, тот пришлет ``Greetings!`` в ответ Команды - это автоматически обрабатываемые сообщения. Вы могли заметить, что при создании бота мы использовали префикс. Именно тут он и используется. Вся разница заключается в части, начинающейся с :func:`bot.command` Первая строка просто импортирует библиотеку. Если при этом вылетает `ModuleNotFoundError` или `ImportError`, тогда вам стоит посмотреть раздел :ref:`vk-intro`. Тут много чего происходит, так что разложим все по полкам. Команды создаются с помощью декоратора :func:`Bot.command`, который может принимать несколько аргументов, к примеру :attr:`name`, который мы тут и использовали. По умолчанию он и так примет значения имени функции, так что тут он не особо нужен, но так читабельней На этой странице показано небольшое вступление к библиотеке. Предпологается, что она у вас уже установлена. Если нет, посмотрите :ref:`vk-intro`. Потом мы используем :meth:`Bot.listen()`, чтобы ловить события. В этой библиотеке куча событий. Эта библиотека асинхронная, так что все происходит в стиле "обратного вызова". vk-botting - библиотека с уймой возможностей для создания команд. 