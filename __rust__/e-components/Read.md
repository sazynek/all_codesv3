

// event будут действия по типу clicked, hovered,  auto и т.п.;
// operator будут on like =>
// action будет stop,start // наднный момент их только 2
// separator  будет and // на данный момент он только 1
// target будут любые сущсности идущие после operator
// assignment будут is as
// expression будет operator + target или  operator + action + target или target+assignment+ target
 
// условия:
// 1. после event всегда идёт expression
// 2. после action всегда идёт target
// 3. после operator всегда идет target или action+ target
// 4. separator разделяет 2 или более expression, то есть находится между ними. 
// 5 вытекает из 4 пункта, если expression не разделенны separator, то их стоит интрепретировать, как одно значение.
// 6. при использовании assignment is или as у нас всегда есть 2 target, то есть assignment +target всегда будет равняться велому target. target+ assignment + target. то есть если упроситить, то target после is или это значение, а target перед это ключ, как обычная переменная a=3. вместо равно is. сочетание target+assignment+ target = expression
// 7. assignment as работает, как сказано в 6 правиле, но с небольшим уточнением. по сути выражение справа assignment+target присваивается левому target,но лево выражение можно рассматривать, как алиас правому.   
Например
    #[animator_fn(app as _self)]// используем  _self, чтобы компилятор rust не ругался. использовать self он запрещает, поэтому добавляем _ вначале.
    при заврарачивании выражения when мы используем self.код...  , но у нас сверху указывается макрос animator_fn, он интерпретирует when в rust код, а аргументы внутри говорят, что нужно заменить стандартный self, на app. то есть app выступает, как(as) self. То есть это не обычное присваивание, как в is, а интерпритация значения _self(self), как app app.код...
Например:
    #[animation(group is button_anims and  property  is position_x and  id is button0)]
или
    #[animation(group is 3 and  property  is hallow_world and  id is 2313.0)]
вот пример ещё пример: 
#[when(event operator action target operator target)]
сократим:
#[when(event expression expression)]
ещё сократим
#[when(event expression)] 
получается:
#[when(clicked => stop button_anims on button0)]

В коде используется с ui.button или другими выражениями:
#[when(clicked => stop button_anims on button0)]
ui.button("hallow") // пример