from flask import Flask, request, jsonify # type: ignore
from backend.pizza_system import Pizzaria
import json

app = Flask(__name__)
pizzaria = Pizzaria()


@app.route('/api/pedidos', methods=['POST'])
def adicionar_pedido():
    data = request.json
    nome = data['nome']
    sabor = data['sabor']
    endereco = data['endereco']

    pizzaria.adicionar_pedido(nome, sabor, endereco)
    return jsonify({"status": "success"})


@app.route('/api/pedidos', methods=['GET'])
def listar_pedidos():
    pedidos = pizzaria.todos_pedidos.em_ordem()
    pedidos_data = [{
        "cliente": p.cliente_nome,
        "sabor": p.sabor,
        "endereco": p.endereco,
        "tempo": p.tempo_entrega
    } for p in pedidos]
    return jsonify(pedidos_data)


@app.route('/api/clientes', methods=['GET'])
def listar_clientes():
    clientes_data = []
    for nome, cliente in pizzaria.clientes.items():
        pedidos = cliente.pedidos.em_ordem()
        clientes_data.append({
            "nome": nome,
            "pedidos": [{
                "sabor": p.sabor,
                "endereco": p.endereco,
                "tempo": p.tempo_entrega
            } for p in pedidos]
        })
    return jsonify(clientes_data)


@app.route('/api/pedidos/<int:tempo>', methods=['DELETE'])
def remover_pedido(tempo):
    pizzaria.remover_pedido(tempo)
    return jsonify({"status": "success"})


@app.route('/api/estatisticas', methods=['GET'])
def estatisticas():
    # Implementar similar ao método gerar_estatisticas
    pass


if __name__ == '__main__':
    app.run(debug=True)
