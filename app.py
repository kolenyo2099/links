from flask import Flask, request, jsonify, send_file
from bs4 import BeautifulSoup
import requests
import csv
import re
import networkx as nx

app = Flask(__name__, static_folder='.', static_url_path='')

@app.route('/crawl', methods=['POST'])
def crawl():
    urls = request.json['urls']
    results = []
    for url in urls:
        response = requests.get(url)
        soup = BeautifulSoup(response.text, 'html.parser')
        for link in soup.find_all('a'):
            href = link.get('href')
            if href and href.startswith('http'):
                results.append({
                    'source': url,
                    'target': href,
                })
    return jsonify(results)

def extract_domain(url):
    domain = re.search('https?://([A-Za-z_0-9.-]+).*', url)
    domain = domain.group(1) if domain else None
    if domain and domain.startswith('www.'):
        domain = domain[4:]
    return domain

@app.route('/process_data', methods=['POST'])
def process_data():
    data = request.json['data']
    option = int(request.json['option'])

    for row in data:
        if option == 2:
            row['target'] = extract_domain(row['target'])
        elif option == 3:
            row['source'] = extract_domain(row['source'])
            row['target'] = extract_domain(row['target'])

    return jsonify(data)

@app.route('/export_csv', methods=['POST'])
def export_csv():
    data = request.json['data']
    with open('export.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Source", "Target"])
        for row in data:
            writer.writerow([row['source'], row['target']])
    return send_file('export.csv', as_attachment=True)

@app.route('/export_gexf', methods=['POST'])
def export_gexf():
    data = request.json['data']
    G = nx.DiGraph()
    for row in data:
        G.add_edge(row['source'], row['target'])
    nx.write_gexf(G, "network.gexf")
    return send_file('network.gexf', as_attachment=True)

@app.route('/graph_data', methods=['POST'])
def graph_data():
    data = request.get_json()['data']
    nodes = []
    edges = []
    node_counts = {}

    for row in data:
        node_counts[row['source']] = node_counts.get(row['source'], 0) + 1
        node_counts[row['target']] = node_counts.get(row['target'], 0) + 1
        edges.append({"from": row['source'], "to": row['target']})

    for node_id, count in node_counts.items():
        nodes.append({"id": node_id, "label": node_id, "value": count, "title": f"Edges: {count}"})

    return jsonify({"nodes": nodes, "edges": edges})

@app.route('/')
def home():
    return app.send_static_file('index.html')

if __name__ == '__main__':
    app.run(debug=True)
