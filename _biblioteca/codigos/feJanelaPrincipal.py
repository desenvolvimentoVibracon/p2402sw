# importando bibliotecas
import pickle

import pandas as pd

from PyQt5.QtCore import Qt
from PyQt5.QtGui import QIcon, QPixmap, QBrush, QColor
from PyQt5.QtWidgets import QHeaderView, QApplication, QMessageBox, QHBoxLayout, QMainWindow, QLabel, QVBoxLayout, QWidget, QFileDialog, QComboBox, QTableWidgetItem, QDialog
from PyQt5 import QtGui
from datetime import datetime

import _biblioteca.codigos.beArquivos as beArquivos
import _biblioteca.codigos.feJanelasAux as feJanelasAux
import _biblioteca.codigos.feComponentes as feComponentes

# -----------------------------------------------------------------------------------------------
# classe da janela principal
class JanelaPrincipal(QMainWindow):
    # -----------------------------------------
    # função para inicializar janela 
    def __init__(self):
        super().__init__()
        self.f_inicializaGui()

        # variáveis globais
        # armazena liderança selecionada e lideranças possíveis
        self.propriedadesGerais
        self.quantidadeColunas = 0
        self.linhasCabecalho = []
        # armazena dados importados do masterplan
        self.tabelaLida
        # Inicializa o dicionário de contadores de desvio
        self.contadores_desvio = {
            'Aprovação do cliente': 0,
            'Prazo': 0,
            'Falta de recurso': 0,
            'Qualidade de entrega': 0,
            'Desenvolvimento da tarefa': 0,
            'Mobilização': 0,
            'Elaboração e Verificação': 0,
            'Falta de prioridade': 0,
            'Arquivo técnico': 0,
            'Falha no planejamento': 0
        }
        # armazena status das tarefas
        global statusSelecionados
        statusSelecionados = []
        
        # armazena datas, dia a dia, da primeira à última data lida do masterplan
        global datasCompletas
        datasCompletas = []

    # -----------------------------------------
    # função para inicializar interface
    def f_inicializaGui(self):
        # > be
        self.propriedadesGerais = {
            'gestorDaVez': '',
            'gestoesPossiveis': []
        }
        self.tabelaLida = []

        # > fe
        # título da janela
        self.setWindowTitle('VIBRACON VibraPlan (v.2023.12.11)')

        # ícone
        self.setWindowIcon(QIcon('_biblioteca/arte/logos/iconeVibracon1.ico'))

        # posição e tamanho da janela
        self.setGeometry(100, 100, 1200, 900) 
                
        # bg
        self.bg = QLabel(self)
        self.bg.setGeometry(0, 0, 2500, 2500)
        pixmap = QPixmap('_biblioteca/arte/bg/bgUm.png')
        self.bg.setPixmap(pixmap)
        self.bg.setScaledContents(True)

        # criação de layout
        layout = QVBoxLayout() # vertical

        # espaçamento vertical
        layout.addSpacing(int(self.height() * 0.05))

        # logo vibracon
        linha = QHBoxLayout() # horizontal
        self.logoVibracon = QLabel(self)
        pixmap = QPixmap('_biblioteca/arte/logos/logoPrograma.png')
        self.logoVibracon.setPixmap(pixmap)
        self.logoVibracon.setMaximumHeight(90)
        self.logoVibracon.setMaximumWidth(1000)
        linha.addWidget(self.logoVibracon)
        linha.setAlignment(Qt.AlignRight)

        # pulando para próxima linha
        layout.addLayout(linha)
        linha = QHBoxLayout()
        
        # espaçamento vertical
        layout.addSpacing(int(self.height() * 0.05))

        # canvas para tabela
        self.quadroTarefas = feComponentes.f_criaTabela(self.f_atualizouCelula)
        layout.addWidget(self.quadroTarefas)

        # pulando para próxima linha
        layout.addLayout(linha)
        linha = QHBoxLayout()
    
        # espaçamento vertical
        layout.addSpacing(int(self.height() * 0.05))

        # botao para carregar projeto
        self.botaoCarregaProjeto = feComponentes.f_criaBotao('', '_biblioteca/arte/botoes/botaoAbrirProjeto.png', self.f_janelaCarregaProjeto)
        linha.addWidget(self.botaoCarregaProjeto)

        # botao para salvar projeto
        self.botaoSalvaProjeto = feComponentes.f_criaBotao('', '_biblioteca/arte/botoes/botaoSalvarProjeto.png', self.f_janelaSalvaProjeto)
        linha.addWidget(self.botaoSalvaProjeto)

        # botao para selecionar gestor
        self.botaoSelecionaGestor = feComponentes.f_criaBotao('', '_biblioteca/arte/botoes/botaoMudarLideranca.png', self.f_abreJanelaSelecaoGestor)
        linha.addWidget(self.botaoSelecionaGestor)

        # botao para selecionar masterplan
        self.botaoSelecionaMasterplan = feComponentes.f_criaBotao('', '_biblioteca/arte/botoes/botaoImportarMasterplan.png', self.f_janelaImportaMasterplan)
        linha.addWidget(self.botaoSelecionaMasterplan)

        # botao para mostrar gráficos
        self.botaoMostraGraficos = feComponentes.f_criaBotao('', '_biblioteca/arte/botoes/botaoAderencias.png', self.f_abreJanelaGraficos)
        linha.addWidget(self.botaoMostraGraficos)


        # adicionando linha
        layout.addLayout(linha)
    
        # espaçamento vertical
        layout.addSpacing(int(self.height() * 0.05))

        # container para centralização do layout
        container = QWidget()
        container.setLayout(layout)
        self.setCentralWidget(container)

    # -----------------------------------------
    # função para atualizar exibição do gráfico
    def f_atualizaVisualizacao(self):      
        QMessageBox.information(self, 'AVISO', f'Após confirmar abaixo, aguarde a confirmação enquanto os dados são atualizados!')
        #chamada da função de extrair dados 
        self.f_extraiDadosTotais()
        # limpando tabela
        self.quadroTarefas.clearContents()
        self.quadroTarefas.setRowCount(0)
        self.quadroTarefas.setColumnCount(0)
        
        # variável global que irá armazenar dia a dia do período lido
        datasCompletas = []
        dataAtualSemHora = datetime.today().replace(hour=0, minute=0, second=0, microsecond=0)
        mesAtual = datetime.today().month
        riscoEmDias = 2

        # percorrendo todas as abas até encontrar a desejada
        for indiceTabela, gestaoPossivel in enumerate(self.propriedadesGerais['gestoesPossiveis']):
            # quando encontrar a desejada
            if gestaoPossivel == self.propriedadesGerais['gestorDaVez']:
                # pegando datas mais antiga e nova e gerando delta de 1 dia entre datas
                for dataDaVez in self.tabelaLida[indiceTabela]['dados']['datas']:
                    if not pd.isna(dataDaVez):
                        if isinstance(dataDaVez, pd.Timestamp):
                            dataDaVez = dataDaVez.strftime('%d-%b-%y')
                        pegarMes = datetime.strptime(dataDaVez, '%d-%b-%y').month
                    if mesAtual == pegarMes:
                        datasCompletas.append(dataDaVez)              
                        
                # passando strings para datas
                datasCompletas = sorted([pd.to_datetime(date) for date in datasCompletas], key=lambda x: (pd.isnull(x), x))
                # definindo um intervalo de dadas completas, do primeiro ao último dia dispostos na aba da liderança atual, dia a dia
                primeiraData = datasCompletas[0]
                ultimaData = datasCompletas[-1]
                datasCompletas = pd.date_range(start = primeiraData, end = ultimaData, freq = 'b').strftime('%d-%b').tolist()
                # definindo número de linhas e colunas de acordo com quantidade de tarefas e datas, respectivamente
                self.quantidadeColunas = self.tabelaLida[indiceTabela]['dados'].shape[1] + len(datasCompletas)
                self.quadroTarefas.setRowCount(self.tabelaLida[indiceTabela]['dados'].shape[0])
                self.quadroTarefas.setColumnCount(self.quantidadeColunas)
                self.quadroTarefas.setHorizontalHeaderLabels(['STATUS', 'TAREFAS'] + datasCompletas + ['CAUSA DO DESVIO','PLANO DE AÇÃO'])

                # largura das colunas, em ordem 
                self.quadroTarefas.setColumnWidth(0, 100)  
                self.quadroTarefas.setColumnWidth(1, 300)
                for indiceColuna in range(2, self.quantidadeColunas-1):
                    self.quadroTarefas.setColumnWidth(indiceColuna, 50)
                self.quadroTarefas.setColumnWidth(self.quantidadeColunas-2, 150)
                self.quadroTarefas.setColumnWidth(self.quantidadeColunas-1, 300)

                # listando tarefas
                colunaTarefas = self.tabelaLida[indiceTabela]['dados'].iloc[:, 2]
                colunaPlanoAcao = self.tabelaLida[indiceTabela]['planoDeAcao']
                for indiceTarefa in range(colunaTarefas.shape[0]):
                    # tarefa
                    item = QTableWidgetItem(str(colunaTarefas.iloc[indiceTarefa]))
                    self.quadroTarefas.setItem(indiceTarefa, 1, item)

                    # plano de ação
                    try:
                        item = QTableWidgetItem(str(colunaPlanoAcao[indiceTarefa]))
                        self.quadroTarefas.setItem(indiceTarefa, self.quantidadeColunas-1, item)
                    except: pass
                try:
                    for okDaVez in self.tabelaLida[indiceTabela]['registroDatas']:
                        QApplication.processEvents()
                        if dataTarefaDaVez < dataAtualSemHora:
                            # Marcar como atrasado
                            self.f_coloreStatus(okDaVez['linha'], 'ATRASADO', okDaVez['coluna'])
                        elif (dataTarefaDaVez - dataAtualSemHora) <= riscoEmDias:
                            # Marcar como "RISCO"
                            self.f_coloreStatus(okDaVez['linha'], 'RISCO', okDaVez['coluna'])
                        else:
                            #Marcar como "OK"
                            self.f_coloreStatus(okDaVez['linha'], 'OK', okDaVez['coluna'])
                        
                        # adicionando lista suspensa na coluna de status quando houver tarefa
                        self.f_adicionaListaStatus(indiceTabela, okDaVez['linha'], okDaVez['coluna'])
                        self.f_adicionaListaDesvio(indiceTabela, okDaVez['linha'])

                except Exception:
                    # identificando datas de realização de cada tarefa
                    datasTarefas = self.tabelaLida[indiceTabela]['dados'].iloc[:, 3]
                    for linhaDaVez, dataTarefaDaVez in enumerate(datasTarefas):
                        QApplication.processEvents()
                        try:
                            # selecionando coluna: adicionando 3 devido às colunas de cabeçalho
                            nomeColunaDaVez = dataTarefaDaVez.strftime('%d-%b')
                            indiceColunaDaVez = datasCompletas.index(nomeColunaDaVez) + 3

                            if (dataTarefaDaVez < dataAtualSemHora):
                                # Marcar como "ATRASADO"
                                self.f_coloreStatus(linhaDaVez,  'ATRASADO', indiceColunaDaVez)
                            elif (dataTarefaDaVez - datetime.today()).days <= riscoEmDias:
                                # Marcar como "RISCO"
                                self.f_coloreStatus(linhaDaVez,  'RISCO', indiceColunaDaVez)
                            else:
                                #Marcar como "OK"
                                self.f_coloreStatus(linhaDaVez,  'OK', indiceColunaDaVez)
                            # adicionando lista suspensa na coluna de status quando houver tarefa
                            self.f_adicionaListaStatus(indiceTabela, linhaDaVez, indiceColunaDaVez)
                            self.f_adicionaListaDesvio(indiceTabela, linhaDaVez)
                        except Exception: pass

                break

        # chamada da função que identifica cabeçalho
        #self.f_identificaCabecalho() 

        QMessageBox.information(self, 'AVISO', f'Dados importados com sucesso!\n\n')

    # -----------------------------------------
    # função para pegar dados da planilha para o gráfico pizza
    def f_extraiDadosTotais(self): #FIXME
        planilha = '_aux/testeGrafico.xlsx'  
        df = pd.read_excel(planilha, usecols=[1])
        
        # Imprimir as primeiras linhas do DataFrame
        valores = df.iloc[:, 0].tolist()
        
        # Remover linhas com valores NaN
        df.dropna(inplace=True)
        
        return df

    # ---------------------------------------------------
    # função para adicionar lista suspensa de status
    def f_adicionaListaStatus(self, indiceTabela, linhaDaVez, colunaDaVez):
        # adicionando lista suspensa na coluna de status quando houver tarefa
        dropdown = QComboBox()
        dropdown.setStyleSheet('QComboBox { background-color: transparent; border: 0px}')
        dropdown.addItems(['OK', 'ENTREGUE', 'RISCO', 'ATRASADO', 'EFPRAZO'])
        dropdown.currentIndexChanged.connect(lambda index, indiceTarefas=linhaDaVez: self.f_atualizouListaStatus(indiceTarefas, indiceTabela, colunaDaVez))
        dropdown.setCurrentText(self.tabelaLida[indiceTabela]['dados']['status'][linhaDaVez]) 
        self.quadroTarefas.setCellWidget(linhaDaVez, 0, dropdown)
    
    # -----------------------------------------
    # função trigada quando lista suspensa é atualizada
    def f_atualizouListaStatus(self, linhaDaVez, indiceTabela, colunaDaVez):
        # identificando emissor do sinal de atualização de lista suspensa
        campoListaSuspensa = self.sender()
        valorDaVez = campoListaSuspensa.currentText()

        if isinstance(campoListaSuspensa, QComboBox):
            self.f_coloreStatus(linhaDaVez, valorDaVez, colunaDaVez)
            # texto de status na variável
            self.tabelaLida[indiceTabela]['dados'].iloc[linhaDaVez, 1] = valorDaVez

    # -----------------------------------------
    # função para adicionar lista suspensa de causa de desvio
    def f_adicionaListaDesvio(self, indiceTabela, linhaDaVez): #FIXME 
        # adicionando lista suspensa na coluna de status quando houver tarefa
        dropdown = QComboBox()
        dropdown.setStyleSheet('QComboBox { background-color: transparent; border: 0px}')
        dropdown.addItems(['', 'Aprovação do cliente', 'Prazo', 'Falta de recurso', 'Qualidade de entrega', 'Desenvolvimento da tarefa', 
                           'Mobilização', 'Elaboração e Verificação', 'Falta de prioridade', 'Arquivo técnico', 'Falha no planejamento', ''])
        dropdown.currentIndexChanged.connect(lambda index, linha=linhaDaVez: self.f_atualizouListaDesvio(linha))
        self.quadroTarefas.setCellWidget(linhaDaVez, self.quantidadeColunas-2, dropdown)

    #----------------------------------------------------------------
    # função para armazenar as 
    def f_atualizouListaDesvio(self, linha): 
        # Obtém a opção selecionada
        opcao_selecionada = self.quadroTarefas.cellWidget(linha, self.quantidadeColunas-2).currentText()
        
        # Verifica se a lista de opções selecionadas já foi inicializada
        if 'opcoes_selecionadas' not in self.__dict__:
            self.opcoes_selecionadas = []

        # Verifica se já existe uma opção selecionada para a linha atual
        for item in self.opcoes_selecionadas:
            if item['linha'] == linha:
                # Diminui o contador da opção anterior em 1
                self.contadores_desvio[item['opcao']] -= 1
                break
        
        # Atualiza a opção selecionada e seu respectivo contador
        self.opcoes_selecionadas.append({
            'linha': linha,
            'opcao': opcao_selecionada
        })
        self.contadores_desvio[opcao_selecionada] += 1

        # Exibe a mensagem com os contadores
        mensagem = ''
        for opcao, contador in self.contadores_desvio.items():
            mensagem += f'{opcao}: {contador}\n'

        QMessageBox.information(self, 'Contadores de Desvio', mensagem)

    #-------------------------------------------
    # função para inicializar janela de gráficos
    def f_abreJanelaGraficos(self):
        # chamando classe com janela para seleção do gesto
        try: feJanelasAux.f_plotaAderencias(self, datasCompletas)
        except Exception as erro: QMessageBox.critical(self, 'AVISO', f'Erro ao plotar as aderências.\n\n {str(erro)}')

    # -----------------------------------------
    # função para salvar novas datas modificadas já no vibraplan
    def f_salvaNovasDatas(self):
        #
        registrosDatas = []
        for linhaDaVez in range(self.quadroTarefas.rowCount()):
            for colunaDaVez in range(2, self.quadroTarefas.columnCount()):
                # obtendo valor da célula caso ela exista
                celulaDaVez = self.quadroTarefas.item(linhaDaVez, colunaDaVez)
                if celulaDaVez is not None:
                    if celulaDaVez.text().upper() != ' ' :
                        registrosDatas.append({'linha': linhaDaVez, 'coluna': colunaDaVez})

        # percorrendo todas as abas até encontrar a da liderança atual
        for indiceTabela, gestaoPossivel in enumerate(self.propriedadesGerais['gestoesPossiveis']):

            # quando encontrar a desejada
            if gestaoPossivel == self.propriedadesGerais['gestorDaVez']:
                self.tabelaLida[indiceTabela]['registroDatas'] = registrosDatas
                break

    # -----------------------------------------
    # função para inicializar janela de seleção de gestor
    def f_abreJanelaSelecaoGestor(self):
        # chamando classe com janela para seleção do gesto
        janelaSelecionaGestor = feJanelasAux.JanelaSelecionaGestor(self)
        if janelaSelecionaGestor.exec_() == QDialog.Accepted:
            # salvando datas de tarefas atuais
            self.f_salvaNovasDatas()

            # atualizando
            self.propriedadesGerais['gestorDaVez'] = janelaSelecionaGestor.f_obtemPropriedades()

            # atualizando visualização com o gestor escolhido
            if self.propriedadesGerais['gestorDaVez'] != '':
                self.f_atualizaVisualizacao()

    # -----------------------------------------
    # função para atualizar lista de gestores
    def f_atualizaGestores(self):
        # atualizando lista de abas (gestores)
        self.propriedadesGerais['gestoesPossiveis'] = []
        for tabelaDaVez in self.tabelaLida: self.propriedadesGerais['gestoesPossiveis'].append(tabelaDaVez['gestor'])
        self.propriedadesGerais['gestorDaVez'] = self.propriedadesGerais['gestoesPossiveis'][-2]

    # -----------------------------------------     
    # função trigada quando célula é atualizada       
    def f_atualizouCelula(self):
        # cores de acordo com textos
        textoCor = {'OK': '#2C4594', 'NOK': '#5D9145', 'ENTREGUE': '#5D9145', 'ATRASADO': '#DF6158' , 'RISCO': '#EE964B', 'EFPRAZO': '#942c79', '': '#f7f7f7' }
        
        # percorrendo linhas e colunas da tabela
        for linhaDaVez in range(self.quadroTarefas.rowCount()):
            for colunaDaVez in range(self.quadroTarefas.columnCount()):
                # obtendo valor da célula caso ela exista
                celulaDaVez = self.quadroTarefas.item(linhaDaVez, colunaDaVez)
                if celulaDaVez is not None:
                    celulaDaVezValor = celulaDaVez.text().upper()
                    
                    # se texto da célula atual estiver na lista de cores de acordo com texto, atualizo cores de fundo e da fonte
                    if celulaDaVezValor in textoCor:
                        corDaVez = textoCor[celulaDaVezValor]
                        self.quadroTarefas.item(linhaDaVez, colunaDaVez).setBackground(QBrush(QColor(corDaVez)))
                        self.quadroTarefas.item(linhaDaVez, colunaDaVez).setForeground(QBrush(QColor(corDaVez)))

        # pegando plano de ação
        planoDeAcao = []
        for linhaDaVez in range(self.quadroTarefas.rowCount()):
            try:
                planoDeAcao.append(self.quadroTarefas.item(linhaDaVez, self.quadroTarefas.columnCount()-1).text())
            except:
                planoDeAcao.append('')

        # percorrendo todas as abas até encontrar a desejada
        for indiceTabela, gestaoPossivel in enumerate(self.propriedadesGerais['gestoesPossiveis']):
            # quando encontrar a desejada
            if gestaoPossivel == self.propriedadesGerais['gestorDaVez']:
                self.tabelaLida[indiceTabela]['planoDeAcao'] = planoDeAcao
        planoDeAcao = []

    # -----------------------------------------  
    # função para colorir status de acordo com o definido
    def f_coloreStatus(self, linhaDaVez, valorDaVez, colunaDaVez):          
        # colorindo a data da tarefa da vez
        self.quadroTarefas.setItem(
            linhaDaVez, colunaDaVez,
            QTableWidgetItem(str(valorDaVez))
            )      
    
    # --------------------------------------------
    # função para identificar linhas de cabeçalho
    def f_identificaCabecalho(self):
    # percorrendo as linhas da tabela
        for linhaDaVez in range(self.quadroTarefas.rowCount()):
            # Verificar se todas as letras na linha estão em caixa alta
            linhaTexto = ""
            for coluna in range(self.quadroTarefas.columnCount()):
                try:
                    linhaTexto += str(self.quadroTarefas.item(linhaDaVez, coluna).text())
                except AttributeError:
                    pass

            if linhaTexto.isupper():
                self.f_personalizaCabecalho(linhaDaVez)

    # -----------------------------------------           
    # função para personalização dos cabeçalhos da tabela
    def f_personalizaCabecalho(self, linhaDaVez):
    # percorrendo três primeiras colunas de cabeçalho
        for colunaDaVez in range(0, 3):
            # pegando célula: caso não exista (células vazias), crio
            celulaDaVez = self.quadroTarefas.item(linhaDaVez, colunaDaVez)
            if celulaDaVez is None:
                celulaDaVez = QTableWidgetItem()
                self.quadroTarefas.setItem(linhaDaVez, colunaDaVez, celulaDaVez)
            
            textoCelula = celulaDaVez.text()
            # personalizando: definindo bg, fg e fonte
            if textoCelula.startswith(' '):
                celulaDaVez.setBackground(QtGui.QColor('#20326A'))
            elif textoCelula.startswith('  '):
                celulaDaVez.setBackground(QtGui.QColor('#2C4594'))
            elif textoCelula.startswith('   '):
                celulaDaVez.setBackground(QtGui.QColor('#3B5CC5'))
            elif textoCelula.startswith('    '):
                celulaDaVez.setBackground(QtGui.QColor('#5A76CE'))
            else:
                celulaDaVez.setBackground(QtGui.QColor('#17244D'))
            
            celulaDaVez.setForeground(QtGui.QColor('white'))
            fonteDaVez = celulaDaVez.font()
            fonteDaVez.setBold(True)
            celulaDaVez.setFont(fonteDaVez)
            
    # -----------------------------------------
    # janela para carregar projeto
    def f_janelaCarregaProjeto(self):
        # abrindo janela de diálogo
        caminhoArquivo, _ = QFileDialog.getOpenFileName(self, 'CARREGAR', '', 'Arquivos VibraPlan (*.projVibraPlan);;All Files (*)')

        # caso usuário defina nome e caminho, lendo os dados do projeto
        if caminhoArquivo:
            try:
                with open(caminhoArquivo, 'rb') as file:
                    self.tabelaLida = pickle.load(file)

                # atualizando lista de gestores e visualização da tabela
                self.f_atualizaGestores()
                self.f_atualizaVisualizacao()

            except Exception as erro:
                QMessageBox.critical(self, 'AVISO', f'Falha ao carregar o projeto.\n\n {str(erro)}')
        else:
            QMessageBox.warning(self, 'AVISO', 'Nenhum projeto foi selecionado!')

    # -----------------------------------------
    # janela para salvamento do projeto
    def f_janelaSalvaProjeto(self):
        # salvando datas de tarefas atuais
        self.f_salvaNovasDatas()

        # abrindo janela de diálogo
        caminhoArquivo, _ = QFileDialog.getSaveFileName(self, 'SALVAR', '', 'Arquivos VibraPlan (*.projVibraPlan);;All Files (*)')

        # caso usuário defina nome e caminho, salvando os dados do projeto
        if caminhoArquivo:
            try:
                with open(caminhoArquivo, 'wb') as file:
                    pickle.dump(self.tabelaLida, file)

                QMessageBox.information(self, 'AVISO', f'Sucesso ao salvar o projeto!\n\n {caminhoArquivo}')
            except Exception as erro:
                QMessageBox.critical(self, 'AVISO', f'Falha ao carregar o projeto.\n\n {str(erro)}')
        else:
            QMessageBox.warning(self, 'AVISO', 'Projeto sem salvar!')

    # -----------------------------------------
    # janela para abertura do arquivo masterplan
    def f_janelaImportaMasterplan(self):
        opcoes = QFileDialog.Options()
        opcoes |= QFileDialog.ReadOnly

        # abrindo janela de diálogo
        caminhoArquivo, _ = QFileDialog.getOpenFileName(
            self,
            'IMPORTAR PROJETO',
            '',
            'Arquivos exportados do Masterplan (*.xlsx *.xls)',
            options = opcoes
        )

        # tentando abrir arquivo caso selecionado
        if caminhoArquivo:
            try:
                # abrindo arquivo e lendo cada aba presente
                self.tabelaLida = beArquivos.f_abrePlanilha(caminhoArquivo)

                # 
                self.f_atualizaGestores()

                # atualizando exibição
                self.f_atualizaVisualizacao()

            except Exception as erro:
                self.propriedadesGerais['gestoesPossiveis'] = []
                self.propriedadesGerais['gestorDaVez'] = ''
                QMessageBox.warning(self, 'AVISO', 'Erro ao abrir o MasterPlan\n\n' + str(erro))

        else:
            QMessageBox.warning(self, 'AVISO', 'Nenhum MasterPlan foi selecionado!')