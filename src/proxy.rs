//! Este módulo gerencia o rodízio de proxies autenticados.
//! Ele pré-aloca clientes HTTP para evitar sobrecarga de rede.

use reqwest::Client;
use std::sync::atomic::{AtomicUsize, Ordering};
use std::sync::Arc;

/// Estrutura responsável por distribuir requisições entre diferentes proxies.
pub struct RoteadorDeProxy {
    // Arc para que a lista possa ser compartilhada entre várias threads com segurança.
    clientes: Arc<Vec<Client>>,
    // O contador atômico permite incrementar o índice sem travar o programa.
    contador: AtomicUsize,
}

impl RoteadorDeProxy {
    /// Cria um novo roteador a partir de uma lista de strings no formato IP:PORTA:USER:PASS.
    pub fn new(proxies: Vec<String>) -> Self {
        let clientes: Vec<Client> = proxies
            .into_iter()
            .map(|linha| {
                let partes: Vec<&str> = linha.split(':').collect();
                
                // URL no formato padrão: http://usuario:senha@ip:porta
                let url = format!(
                    "http://{}:{}@{}:{}", 
                    partes[2], partes[3], partes[0], partes[1]
                );

                // Cliente configurado com proxy específico.
                Client::builder()
                    .proxy(reqwest::Proxy::all(url).expect("URL de proxy inválida"))
                    .build()
                    .expect("Erro ao construir cliente HTTP")
            })
            .collect();

        Self {
            clientes: Arc::new(clientes),
            contador: AtomicUsize::new(0),
        }
    }

    /// Retorna o próximo cliente da lista usando a estratégia Round-Robin.
    pub fn proximo(&self) -> Client {
        // Incrementa o contador de forma segura entre threads.
        let indice_atual = self.contador.fetch_add(1, Ordering::Relaxed);
        
        // Usa o módulo (%) para garantir que o índice circule na lista.
        let indice = indice_atual % self.clientes.len();
        
        // Retorna um clone do cliente (que compartilha o pool de conexões).
        self.clientes[indice].clone()
    }
}