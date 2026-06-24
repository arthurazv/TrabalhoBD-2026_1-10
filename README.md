# NullBank - Sistema de Controle Bancário

Projeto final da disciplina de Banco de Dados, período 2026.1, do curso de Engenharia da Computação do Campus de Sobral. 

Este sistema gerencia as operações de uma instituição bancária (NullBank), suportando o cadastro de agências, funcionários, clientes e o processamento de transações financeiras.

**Professor:** Fernando Rodrigues de Almeida Júnior
**Equipe**
- Antônio Kildere Sousa Menezes – Matrícula: 567258
- José Arthur Gomes Azevedo – Matrícula: 567419
- Daniel Neco Silva – Matrícula: 568270

---

## 🛠 Tecnologias Utilizadas

*   **Frontend:** Python (Streamlit)
*   **Banco de Dados:** MySQL (versão 5.7+)
*   **Ferramenta CASE:** MySQL Workbench
*   **Infraestrutura:** Docker e Docker Compose

---

## ⚙️ Funcionalidades e Regras de Negócio

O NullBank foi modelado para suportar o ecossistema bancário completo:

*   **Agências e Funcionários:** Controle de agências (com cálculo automático do montante total de salários) e gestão de funcionários classificados por cargos (gerente, atendente ou caixa). Os funcionários podem registrar até 5 dependentes para fins de plano de saúde.
*   **Clientes e Contas:** Um cliente pode possuir no máximo uma conta por agência. O sistema suporta contas-correntes, contas poupança (com taxa de juros) e contas especiais (com limite de crédito). Contas conjuntas são suportadas para até 2 titulares.
*   **Transações:** Registro imutável de saques, depósitos, pagamentos, estornos, transferências e PIX. O saldo da conta reflete automaticamente o conjunto de transações, impedindo saldos negativados (exceto dentro do limite de crédito em contas especiais).

### 🔐 Controle de Acesso
O sistema implementa três níveis hierárquicos de acesso:
1.  **DBA (Administrador):** Acesso total ao sistema e banco de dados via credenciais `Admin` / `Root`.
2.  **Funcionários (Login via Matrícula):**
    *   *Gerentes:* Cadastram contas, clientes e funcionários, mas não realizam movimentações financeiras diretas.
    *   *Caixas:* Acesso irrestrito às transações financeiras das contas da sua respectiva agência.
    *   *Atendentes:* Acesso exclusivo de leitura para consultas de contas e saldos na sua agência.
3.  **Clientes (Login via CPF):** Acesso às suas próprias contas para visualização e operações, com tela de seleção caso possua múltiplas contas.

---

## 📂 Estrutura do Repositório

*   `app.py`: Ponto de entrada da aplicação frontend em Streamlit.
*   `bd.mwb`: Arquivo de modelagem conceitual/física desenvolvida no MySQL Workbench.
*   `bd.sql`: Scripts contendo a DDL (criação das tabelas) e DML (povoamento inicial do banco). O banco é nomeado como `Equipe567258`.
*   `Consultas.sql`: Arquivo contendo todas as consultas solicitadas nas especificações, além da criação de visões (views), gatilhos (triggers) para atualização de saldos e a transação segura para transferência entre contas.
*   `requirements.txt`: Dependências Python necessárias para rodar o projeto.
*   `docker-compose.yml` e `Dockerfile`: Arquivos para orquestração do ambiente de desenvolvimento.

## 🚀 Como Executar o Projeto Localmente

### Pré-requisitos
Para executar este sistema em sua máquina local, você precisa ter instalado:
*   [Docker](https://www.docker.com/)
*   [Docker Compose](https://docs.docker.com/compose/)

### Passo 1: Iniciar os Containers (Banco + Frontend)
Na pasta raiz do projeto, execute o comando abaixo no terminal para construir a imagem do Streamlit e subir o banco de dados MySQL e o frontend:
```bash
docker compose up -d --build
```

### Passo 2: Inicializar o Banco de Dados (SQL)
Após os containers estarem rodando, é necessário criar a estrutura e os dados do banco de dados executando as queries SQL. 

1. Conecte-se ao servidor MySQL local (`localhost:3306`) usando uma ferramenta cliente (como o **MySQL Workbench** ou **DBeaver**) com as seguintes credenciais:
   *   **Usuário:** `root`
   *   **Senha:** `Root`
2. Execute o conteúdo do arquivo **`bd.sql`** para criar as tabelas e povoar os dados iniciais do NullBank.
3. Execute o conteúdo do arquivo **`Consultas.sql`** para registrar os Triggers, Views, a Procedure de Transferência e carregar as consultas padrão.

### Passo 3: Acessar a Aplicação
Com o banco populado e configurado, acesse o frontend da aplicação em seu navegador através do link:
👉 **[http://localhost:8501](http://localhost:8501)**

*(Nota: Caso deseje rodar a aplicação nativamente sem o Docker, certifique-se de ter o Python 3.11+ instalado, configure as variáveis de ambiente em um arquivo `.env` baseado no `env.example`, crie um ambiente virtual, instale as dependências com `pip install -r requirements.txt` e execute `streamlit run app.py`).*


---

## 🔑 Credenciais Padrão para Teste

Para facilitar a validação de todas as regras de negócio e níveis de acesso exigidos no enunciado, utilize as credenciais padrão já populadas no banco:

| Nível de Acesso | Tipo de Login / Username | Usuário (Login) | Senha |
| :--- | :--- | :--- | :--- |
| **Administrador / DBA** | Username | `Admin` | `Root` |
| **Gerente** | Matrícula | `MAT1001` | `a1b2c3d4e5f6` |
| **Caixa** | Matrícula | `MAT1002` | `f6e5d4c3b2a1` |
| **Atendente** | Matrícula | `MAT1003` | `c1b2a3d4e5f6` |
| **Cliente (Camila Rocha)** | CPF | `01234567890` | `hashsenha123` |