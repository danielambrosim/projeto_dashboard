from app.services.analysis_service import analisar_excel, analisar_word

# Teste análise de Excel
print("=== Testando análise de Excel ===")
# Use um arquivo real do seu projeto, coloque o caminho correto
caminho_excel = "app/static/uploads/excel_test.xlsx"
resultado_excel = analisar_excel(caminho_excel, output_folder="app/static/uploads", id_arquivo="teste")
print(resultado_excel)
if resultado_excel.get("grafico"):
    print(f"Gráfico gerado em: app/static/{resultado_excel['grafico']}")

# Teste análise de Word
print("\n=== Testando análise de Word ===")
caminho_word = "app/static/uploads/leilao_teste.docx"
resultado_word = analisar_word(caminho_word)
print(resultado_word)
