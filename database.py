import pyodbc
import os
from dotenv import load_dotenv

# Carrega variáveis de ambiente
load_dotenv()

SERVER = os.environ.get('DB_SERVER')
USERNAME = os.environ.get('DB_USER')
PASSWORD = os.environ.get('DB_PASSWORD')
DATABASE = os.environ.get('DB_NAME')
DATABASE_HML = os.environ.get('DB_NAME_HML')

class DataBase():
    def __init__(self, ambiente='produção'):
        self.conn = None
        self.cur = None
        self.ambiente = ambiente
        self.connect()

    def connect(self):
        try:
            database = DATABASE if self.ambiente == 'produção' else DATABASE_HML
            connectionString = f'DRIVER={{ODBC Driver 18 for SQL Server}};SERVER={SERVER};DATABASE={database};UID={USERNAME};PWD={PASSWORD};TrustServerCertificate=yes;'
            self.conn = pyodbc.connect(connectionString)
            self.cur = self.conn.cursor()
        except Exception as e:
            print(f"Erro ao conectar no banco de dados MS SQL Server: {e}")
            self.cur = None
            self.conn = None
            raise

    def get_employee_data(self, matricula, filial):
        query = """
        SELECT sra.RA_CODFUNC, sra.RA_ADMISSA as Admissao, sra.RA_MAT as Matricula, sra.RA_FILIAL, sra.RA_NOMECMP as NOME 
        FROM SRA010 sra
        join srj010 srj on srj.rj_filial = substring(sra.ra_filial, 1, 3) and srj.rj_funcao = sra.ra_codfunc and srj.d_e_l_e_t_ <> '*'
        WHERE sra.RA_MAT = ?
        AND sra.RA_FILIAL = ?
        AND sra.D_E_L_E_T_ <> '*'
        """
        
        # O like do Protheus com RA_MAT pode ter espaços, mas vamos usar "=" e cuidar dos espaços no front-end ou passar com rpad se necessário.
        # No select enviado, estava LIKE '' e =, vou usar = e os params.
        
        try:
            self.cur.execute(query, (matricula, filial))
            row = self.cur.fetchone()
            if row:
                return {
                    "codfunc": row.RA_CODFUNC,
                    "admissao": row.Admissao,
                    "matricula": row.Matricula,
                    "filial": row.RA_FILIAL,
                    "nome": row.NOME.strip() if row.NOME else ""
                }
            return None
        except Exception as e:
            print(f"Erro ao executar query no banco: {e}")
            return None

    def commit_close(self):
        if self.conn:
            self.conn.commit()

    def rollback_close(self):
        if self.conn:
            self.conn.rollback()

    def close(self):
        if self.cur:
            self.cur.close()
        if self.conn:
            self.conn.close()
        self.cur = None
        self.conn = None

    def __del__(self):
        self.rollback_close()
