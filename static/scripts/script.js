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

function OpenRandomModal(){
    const modal = document.getElementById('modalconfirmation2')
    modal.showModal()
}
function CloseRandomModal(){
    const modal = document.getElementById('modalconfirmation2')
    modal.close()
}
function OpenModalMeetings(){
    const modal = document.getElementById('modalcreatemeetings')
    modal.showModal()
}
function CloseModalMeetings(){
    const modal = document.getElementById('modalcreatemeetings')
    modal.close()
}
function OpenModalEditMeeting(Meetingid){
    const modal = document.getElementById('modaleditmeeting')
    const Meetingidinput = document.getElementById('meeting-id')

    Meetingidinput.value = Meetingid

    modal.showModal()
}
function CloseModalEditMeeting(){
    const modal = document.getElementById('modaleditmeeting')
    modal.close()
}
function Openmodalchamada(){
    const modal = document.getElementById('modalchamada')
    modal.showModal() 
}
function Closemodalchamada(){
    const modal = document.getElementById('modalchamada')
    modal.close() 
}
function OpenModalDeleteCrismando(){
    const modal = document.getElementById('deletecrismandoconfirmation')
    modal.showModal()   
}
function CloseModalDeleteCrismando(){
    const modal = document.getElementById('deletecrismandoconfirmation')
    modal.close()   
}
function openEditModal(id, tema) {
    const modal = document.getElementById('modalEscolhaTurma');
    const modalIdInput = document.getElementById('modalEncontroId');
    modalIdInput.value = id;
    modal.showModal();
}
function closeEditModal() {
    const modal = document.getElementById('modalEscolhaTurma');
    modal.close();
}
 function OpenModalconfirmationreset(){
    const modal = document.getElementById('deletesystem');
    modal.showModal();
}
 function CloseModalconfirmationreset(){
    const modal = document.getElementById('deletesystem');
    modal.close();
}
    // Funções do Modal Global de Edição
    const modalEditGlobal = document.getElementById('modaledit-global');
    const inputId = document.getElementById('crismando-id-input');
    const displayNome = document.getElementById('nome-crismando-display');
    const deleteNome = document.getElementById('nome-crismando-delete');
    const formDelete = document.getElementById('form-delete');

    function OpenEditCrismandos(id, nome) {
        inputId.value = id;
        displayNome.textContent = nome;
        deleteNome.textContent = nome;
        
        // Atualiza a rota de exclusão se necessário (exemplo baseando na lógica anterior)
        // Se a sua rota for /deletecrismando/<id>, você pode setar aqui:
        // formDelete.action = "/deletecrismando/" + id;
        
        modalEditGlobal.showModal();
    }

    function CloseEditCrismandos() {
        modalEditGlobal.close();
    }

    // Modal de Confirmação de Exclusão
    const modalDelete = document.getElementById('deletecrismandoconfirmation');
    function OpenModalDeleteCrismando() {
        modalDelete.showModal();
    }
    function CloseModalDeleteCrismando() {
        modalDelete.close();
    }

    // Outros modais
    function OpenModalEditCrismandos() { document.getElementById('modaleditcrismandos').showModal(); }
    function CloseModalEditCrismandos() { document.getElementById('modaleditcrismandos').close(); }
    function OpenRandomModal() { document.getElementById('modalconfirmation2').showModal(); }
    function CloseRandomModal() { document.getElementById('modalconfirmation2').close(); }