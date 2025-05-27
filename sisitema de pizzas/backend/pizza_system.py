import sqlite3

# Conexão com banco SQLite
conn = sqlite3.connect("pizza_tree.db")
cursor = conn.cursor()

# Tabelas
cursor.execute('''
CREATE TABLE IF NOT EXISTS clientes (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    nome TEXT UNIQUE
)
''')

cursor.execute('''
CREATE TABLE IF NOT EXISTS pedidos (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    cliente_id INTEGER,
    sabor TEXT,
    endereco TEXT,
    tempo_entrega INTEGER,
    FOREIGN KEY (cliente_id) REFERENCES clientes(id)
)
''')

conn.commit()

# Classes para a árvore binária


class NoPedido:
    def __init__(self, pedido):
        self.pedido = pedido
        self.esquerda = None
        self.direita = None


class ArvorePedidos:
    def __init__(self):
        self.raiz = None

    # Inserção na árvore (ordenado por tempo de entrega)
    def inserir(self, pedido):
        if self.raiz is None:
            self.raiz = NoPedido(pedido)
        else:
            self._inserir_recursivo(self.raiz, pedido)

    def _inserir_recursivo(self, no, pedido):
        if pedido.tempo_entrega < no.pedido.tempo_entrega:
            if no.esquerda is None:
                no.esquerda = NoPedido(pedido)
            else:
                self._inserir_recursivo(no.esquerda, pedido)
        else:
            if no.direita is None:
                no.direita = NoPedido(pedido)
            else:
                self._inserir_recursivo(no.direita, pedido)

    # Remoção na árvore
    def remover(self, tempo_entrega):
        self.raiz = self._remover_recursivo(self.raiz, tempo_entrega)

    def _remover_recursivo(self, no, tempo_entrega):
        if no is None:
            return no

        if tempo_entrega < no.pedido.tempo_entrega:
            no.esquerda = self._remover_recursivo(no.esquerda, tempo_entrega)
        elif tempo_entrega > no.pedido.tempo_entrega:
            no.direita = self._remover_recursivo(no.direita, tempo_entrega)
        else:
            # Nó com apenas um filho ou nenhum
            if no.esquerda is None:
                return no.direita
            elif no.direita is None:
                return no.esquerda

            # Nó com dois filhos: pega o sucessor in-order (menor na subárvore direita)
            temp = self._min_valor_no(no.direita)
            no.pedido = temp.pedido
            no.direita = self._remover_recursivo(
                no.direita, temp.pedido.tempo_entrega)

        return no

    def _min_valor_no(self, no):
        atual = no
        while atual.esquerda is not None:
            atual = atual.esquerda
        return atual

    # Busca na árvore
    def buscar(self, tempo_entrega):
        return self._buscar_recursivo(self.raiz, tempo_entrega)

    def _buscar_recursivo(self, no, tempo_entrega):
        if no is None:
            return None
        if no.pedido.tempo_entrega == tempo_entrega:
            return no.pedido
        elif tempo_entrega < no.pedido.tempo_entrega:
            return self._buscar_recursivo(no.esquerda, tempo_entrega)
        else:
            return self._buscar_recursivo(no.direita, tempo_entrega)

    # Percursos na árvore
    def em_ordem(self):
        resultado = []
        self._em_ordem_recursivo(self.raiz, resultado)
        return resultado

    def _em_ordem_recursivo(self, no, resultado):
        if no:
            self._em_ordem_recursivo(no.esquerda, resultado)
            resultado.append(no.pedido)
            self._em_ordem_recursivo(no.direita, resultado)

    def pre_ordem(self):
        resultado = []
        self._pre_ordem_recursivo(self.raiz, resultado)
        return resultado

    def _pre_ordem_recursivo(self, no, resultado):
        if no:
            resultado.append(no.pedido)
            self._pre_ordem_recursivo(no.esquerda, resultado)
            self._pre_ordem_recursivo(no.direita, resultado)

    def pos_ordem(self):
        resultado = []
        self._pos_ordem_recursivo(self.raiz, resultado)
        return resultado

    def _pos_ordem_recursivo(self, no, resultado):
        if no:
            self._pos_ordem_recursivo(no.esquerda, resultado)
            self._pos_ordem_recursivo(no.direita, resultado)
            resultado.append(no.pedido)

# Classes do sistema


class Pedido:
    def __init__(self, sabor, endereco, tempo_entrega, cliente_nome):
        self.sabor = sabor
        self.endereco = endereco
        self.tempo_entrega = tempo_entrega
        self.cliente_nome = cliente_nome

    def __str__(self):
        return f"{self.cliente_nome}: {self.sabor} - {self.endereco} ({self.tempo_entrega} min)"


class Cliente:
    def __init__(self, nome):
        self.nome = nome
        self.pedidos = ArvorePedidos()  # Agora usando árvore binária


class Pizzaria:
    def __init__(self):
        self.clientes = {}
        # Árvore com todos os pedidos ordenados por tempo
        self.todos_pedidos = ArvorePedidos()

    def calcular_tempo_entrega(self, endereco):
        distancias = {
            "asa norte": 2, "asa sul": 5, "lago norte": 7,
            "lago sul": 12, "sudoeste": 10, "cruzeiro": 11,
            "noroeste": 4, "águas claras": 23, "taguatinga": 25,
            "samambaia": 30, "ceilândia": 35, "gama": 40
        }
        tempo_preparo = 15
        tempo_por_km = 2
        distancia = distancias.get(endereco.lower(), 10)
        return tempo_preparo + distancia * tempo_por_km

    def adicionar_pedido(self, nome_cliente, sabor, endereco):
        tempo = self.calcular_tempo_entrega(endereco)

        # Verifica ou insere cliente no banco
        cursor.execute("SELECT id FROM clientes WHERE nome = ?",
                       (nome_cliente,))
        cliente = cursor.fetchone()

        if cliente:
            cliente_id = cliente[0]
        else:
            cursor.execute(
                "INSERT INTO clientes (nome) VALUES (?)", (nome_cliente,))
            cliente_id = cursor.lastrowid
            conn.commit()
            self.clientes[nome_cliente] = Cliente(nome_cliente)

        # Insere pedido no banco
        cursor.execute('''
            INSERT INTO pedidos (cliente_id, sabor, endereco, tempo_entrega)
            VALUES (?, ?, ?, ?)
        ''', (cliente_id, sabor, endereco, tempo))
        conn.commit()

        # Cria objeto Pedido e adiciona nas árvores
        novo_pedido = Pedido(sabor, endereco, tempo, nome_cliente)

        # Adiciona na árvore do cliente
        if nome_cliente in self.clientes:
            self.clientes[nome_cliente].pedidos.inserir(novo_pedido)
        else:
            self.clientes[nome_cliente] = Cliente(nome_cliente)
            self.clientes[nome_cliente].pedidos.inserir(novo_pedido)

        # Adiciona na árvore geral de pedidos
        self.todos_pedidos.inserir(novo_pedido)

        print(
            f"✅ Pedido de {sabor} adicionado para {nome_cliente} ({tempo} min).")

    def remover_pedido(self, tempo_entrega):
        # Busca o pedido na árvore geral
        pedido = self.todos_pedidos.buscar(tempo_entrega)
        if pedido:
            # Remove da árvore do cliente
            if pedido.cliente_nome in self.clientes:
                self.clientes[pedido.cliente_nome].pedidos.remover(
                    tempo_entrega)

            # Remove da árvore geral
            self.todos_pedidos.remover(tempo_entrega)

            # Remove do banco de dados
            cursor.execute(
                "DELETE FROM pedidos WHERE tempo_entrega = ?", (tempo_entrega,))
            conn.commit()
            print(f"Pedido removido com sucesso: {pedido}")
        else:
            print("Pedido não encontrado.")

    def buscar_pedido_por_tempo(self, tempo_entrega):
        pedido = self.todos_pedidos.buscar(tempo_entrega)
        if pedido:
            print(f"Pedido encontrado: {pedido}")
        else:
            print("Pedido não encontrado.")

    def mostrar_estrutura(self):
        print("\n🌳 Estrutura de Pedidos por Cliente:")
        cursor.execute("SELECT id, nome FROM clientes")
        clientes = cursor.fetchall()

        for cid, nome in clientes:
            print(f"\n👤 Cliente: {nome}")
            if nome in self.clientes:
                print("  Pedidos (ordenados por tempo de entrega):")
                pedidos = self.clientes[nome].pedidos.em_ordem()
                for i, pedido in enumerate(pedidos, 1):
                    print(
                        f"   🍕 Pedido {i}: {pedido.sabor} - {pedido.endereco} - ETA: {pedido.tempo_entrega} min")
            else:
                print("  Nenhum pedido na árvore (pode haver no banco de dados)")

    def mostrar_arvore_completa(self):
        print("\n🌲 Árvore Completa de Todos os Pedidos (ordenados por tempo):")
        pedidos = self.todos_pedidos.em_ordem()
        for i, pedido in enumerate(pedidos, 1):
            print(f"  {i}. {pedido}")

    def gerar_estatisticas(self):
        print("\n📊 Estatísticas:")
        cursor.execute('''
            SELECT c.nome, COUNT(p.id) AS total, AVG(p.tempo_entrega) AS media
            FROM clientes c
            JOIN pedidos p ON c.id = p.cliente_id
            GROUP BY c.id
        ''')
        dados = cursor.fetchall()

        if not dados:
            print("Nenhum dado para exibir.")
            return

        maior = max(dados, key=lambda x: x[1])
        menor = min(dados, key=lambda x: x[2])

        for nome, total, media in dados:
            print(f"👤 {nome}: {total} pedidos, tempo médio {round(media, 2)} min")

        print(f"\n🏆 Cliente com mais pedidos: {maior[0]} ({maior[1]} pedidos)")
        print(
            f"⏱ Cliente mais rápido (média): {menor[0]} ({round(menor[2], 2)} min)")

        # Estatísticas da árvore
        pedidos_em_ordem = self.todos_pedidos.em_ordem()
        if pedidos_em_ordem:
            print("\n📈 Estatísticas da Árvore:")
            print(f"Total de pedidos na árvore: {len(pedidos_em_ordem)}")
            print(
                f"Pedido mais rápido: {pedidos_em_ordem[0].tempo_entrega} min")
            print(
                f"Pedido mais demorado: {pedidos_em_ordem[-1].tempo_entrega} min")


# Interface do sistema
pizzaria = Pizzaria()

# Carregar dados do banco para as árvores
cursor.execute(
    "SELECT c.nome, p.sabor, p.endereco, p.tempo_entrega FROM clientes c JOIN pedidos p ON c.id = p.cliente_id")
for nome, sabor, endereco, tempo in cursor.fetchall():
    pedido = Pedido(sabor, endereco, tempo, nome)
    if nome not in pizzaria.clientes:
        pizzaria.clientes[nome] = Cliente(nome)
    pizzaria.clientes[nome].pedidos.inserir(pedido)
    pizzaria.todos_pedidos.inserir(pedido)

while True:
    print("\n🍕 Sistema de Pedidos (Árvore Binária + SQLite)")
    print("1️⃣ Novo Pedido")
    print("2️⃣ Mostrar Árvore de Pedidos por Cliente")
    print("3️⃣ Mostrar Árvore Completa de Pedidos")
    print("4️⃣ Buscar Pedido por Tempo de Entrega")
    print("5️⃣ Remover Pedido por Tempo de Entrega")
    print("6️⃣ Ver Estatísticas")
    print("7️⃣ Sair")

    op = input("Escolha: ")

    if op == "1":
        nome = input("Nome do cliente: ")
        sabor = input("Sabor da pizza: ")
        endereco = input("Bairro de entrega: ")
        pizzaria.adicionar_pedido(nome, sabor, endereco)
    elif op == "2":
        pizzaria.mostrar_estrutura()
    elif op == "3":
        pizzaria.mostrar_arvore_completa()
    elif op == "4":
        try:
            tempo = int(input("Tempo de entrega para buscar: "))
            pizzaria.buscar_pedido_por_tempo(tempo)
        except ValueError:
            print("Por favor, insira um número válido.")
    elif op == "5":
        try:
            tempo = int(input("Tempo de entrega para remover: "))
            pizzaria.remover_pedido(tempo)
        except ValueError:
            print("Por favor, insira um número válido.")
    elif op == "6":
        pizzaria.gerar_estatisticas()
    elif op == "7":
        print("👋 Encerrando...")
        break
    else:
        print("❌ Opção inválida.")

# Fecha o banco
conn.close()
