function Openmodalmasterpassword(event){
    // 1. OBRIGATÓRIO: Impede que o formulário seja submetido imediatamente
    event.preventDefault(); 
    // aqui é definido para os inputs ocultos do modal receberem o valor do input principal, assim quando chamar no app.py irá funcionar, por ser forms diferentes. O primeiro se torna "visual"
    const nome = document.form1.nome.value
    const senha = document.form1.senha.value
    document.getElementById("modal-nome").value = nome
    document.getElementById("modal-senha").value = senha
    // aqui abre o modal
    const modal = document.getElementById("modalcreateaccount")
    modal.showModal()
}

function Closemodalmasterpassword(){
    const modal = document.getElementById("modalcreateaccount")
    modal.close();
}

function OpenModalTurmas(){
    const modal = document.getElementById("modalturmas")
    modal.showModal();
}
function CloseModalTurmas(){
    const modal = document.getElementById("modalturmas")
    modal.close(); 
}
function OpenModalEditCrismandos(){
    const modal = document.getElementById("modaleditcrismandos")
    modal.showModal();
}
function CloseModalEditCrismandos(){
    const modal = document.getElementById("modaleditcrismandos")
    modal.close(); 
}
function OpenModalConfirmation(){
    const modal = document.getElementById("modalconfirmation")
    modal.showModal();   
}
function CloseModalConfirmation(){
    const modal = document.getElementById("modalconfirmation")
    modal.close();   
}
function OpenEditCrismandos(crismandoId) {
  const dialog = document.getElementById('modaledit-global');
  const inputCrismandoId = document.getElementById('crismando-id-input');
  const deleteForm = document.getElementById('form-delete-crismando');

  // Define o ID do crismando no formulário de troca
  inputCrismandoId.value = crismandoId;

  // 2. Define onde o formulário de exclusão vai enviar
  document.getElementById('form-delete').action = `/deletecrismandos/${crismandoId}`;

  // 3. Abre o diálogo
  document.getElementById('modaledit-global').showModal();
}

function CloseEditCrismandos() {
  const dialog = document.getElementById('modaledit-global');
  dialog.close();
}
