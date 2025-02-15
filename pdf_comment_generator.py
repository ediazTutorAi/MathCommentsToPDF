import subprocess
import os

class MathPDFGenerator:
    def __init__(self):
        pass

    def create_pdf_from_latex(self,code,output_pdf_page='comments.pdf'):
        # Define LaTeX content
        latex_content = r"""
        \documentclass[20pt]{extarticle}
        \usepackage{xcolor}
        \usepackage[a4paper,margin=0.5in]{geometry}
        \begin{document}
 
        Comment by Instructor: """+code+r"""

        \end{document}
        """

        # Write LaTeX content to a .tex file
        tex_file = 'comments.tex'
        with open(tex_file, 'w') as f:
            f.write(latex_content)

        # Compile the LaTeX document to a PDF using pdflatex
        try:
            output_pdf_page = subprocess.run(['pdflatex','-interaction=nonstopmode', tex_file], check=True)
            
            print("PDF created successfully.")
        except subprocess.CalledProcessError as e:
            print(f"An error occurred while compiling the LaTeX document: {e}")

        # Optional: Cleanup auxiliary files generated by LaTeX
        aux_files = ['comments.aux', 'comments.log', 'comments.tex']
        for aux_file in aux_files:
            try:
                os.remove(aux_file)
            except OSError:
                pass

        
        return os.path.abspath('comments.pdf')       


