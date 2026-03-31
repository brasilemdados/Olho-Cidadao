mod proxy; 

use proxy::RoteadorDeProxy;
use std::fs;

#[tokio::main]
async fn main() {
    // Lendo o arquivo de proxies
    // O expect interrompe o programa com uma mensagem se o arquivo não existir
    let conteudo = fs::read_to_string("proxies.txt")
        .expect("Erro: O arquivo 'proxies.txt' não foi encontrado na raiz do projeto.");

    // Transformando o texto em uma lista de Strings (Vec<String>)
    let lista_proxies: Vec<String> = conteudo
        .lines()                         
        .filter(|l| !l.trim().is_empty()) 
        .map(|l| l.to_string())          
        .collect();                    

    // Inicializa o Roteador
    let roteador = RoteadorDeProxy::new(lista_proxies);

    println!("{}",conteudo);
}