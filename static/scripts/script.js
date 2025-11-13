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