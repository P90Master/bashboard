var sio = io.connect('http://127.0.0.1:5000');
var path = window.location.pathname;

sio.on('connect', () => {
  sio.emit('join_thread', {'path': path})
});

sio.on('message', (msg) => {
  const new_msg_id = document.createElement('div');
  new_msg_id.setAttribute("class", "col-auto");
  new_msg_id.innerText = msg['id'];

  const new_msg_separator = document.createElement('div');
  new_msg_separator.setAttribute("class", "col-auto");
  new_msg_separator.innerText = '>';

  const new_msg_text = document.createElement('div');
  new_msg_text.setAttribute("class", "col-auto");
  new_msg_text.innerText = msg['text'];

  const new_msg = document.createElement('div');
  new_msg.setAttribute("class", "row g-2");
  new_msg.innerHTML += new_msg_id.outerHTML + new_msg_separator.outerHTML + new_msg_text.outerHTML

	$(".messages").append(new_msg);

  window.scrollBy(0, window.innerHeight);
});

sio.on('redirect', (destination) => {
  window.location.href = destination['path'];
});

sio.on('cmd_output_clear', () => {
  $(".cmd_output").empty();
});

sio.on('cmd_output', (data) => {
  $(".cmd_output").empty();
  var text = data['text']

  for (let i = 0; i < text.length; i++) {
    var cmd_msg = document.createElement('div');
    cmd_msg.setAttribute("class", "row g-2");

    var cmd_msg_text = document.createElement('div');
    cmd_msg_text.setAttribute("class", "col-auto");
    cmd_msg_text.innerText = text[i];

    cmd_msg.innerHTML += cmd_msg_text.outerHTML

    $(".cmd_output").append(cmd_msg);
  }

  window.scrollBy(0, window.innerHeight);
});

$('#input-textarea').keypress(function(e){
  if(e.which == 13 && !e.shiftKey){
    var text = $('#input-textarea').val();
    sio.emit('message', {'text': text, 'path': path});
    $('#input-textarea').val('');

    return false;
  }
});

const tx = document.getElementsByTagName("textarea");
for (let i = 0; i < tx.length; i++) {
  tx[i].setAttribute("style", "height:" + (tx[i].scrollHeight) + "px;overflow-y:hidden;");
  tx[i].addEventListener("input", OnInput, false);
}

function OnInput() {
  this.style.height = 0;
  this.style.height = (this.scrollHeight) + "px";
}
