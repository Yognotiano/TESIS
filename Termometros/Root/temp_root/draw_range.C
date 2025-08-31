// draw_range.C — Abrir archivo, cortar por rango [start,end] y graficar/guardar

#include <TFile.h>
#include <TTree.h>
#include <TCut.h>
#include <TString.h>
#include <TSystem.h>
#include <iostream>
#include <cstdio>
#include <cstring>

/** 1: parse_dt
    Parsea "YYYY-MM-DD HH:MM:SS" a (ymd, tsec). Devuelve true si ok.
    - std::sscanf(): extrae enteros desde el string.
*/
static bool parse_dt(const char* dt, int& ymd, int& tsec){
  if(!dt || !*dt) return false;
  int Y,M,D,h,m,s;
  if(std::sscanf(dt, "%d-%d-%d %d:%d:%d", &Y,&M,&D,&h,&m,&s) != 6) return false;
  ymd  = Y*10000 + M*100 + D;
  tsec = h*3600 + m*60 + s;
  return true;
}

/** 2: build_sel
    Construye el TCut para el rango [start,end]. Si 'end' es vacío, usa
    "desde start hasta el final". Si file_id>=0, lo agrega al corte.
    - TCut: clase de ROOT para selecciones (acepta strings C).
*/
static TCut build_sel(const char* start, const char* end, int file_id){
  int ymd_s=0, ts_s=0, ymd_e=0, ts_e=0;
  if(!parse_dt(start, ymd_s, ts_s)){
    std::cerr << "[ERROR] Formato start inválido: " << (start?start:"(null)") << "\n";
    return TCut("");
  }
  bool has_end = (end && *end && parse_dt(end, ymd_e, ts_e));

  // Alias útil en el árbol (lo volvemos a definir en draw_range):
  // ymd = year*10000 + month*100 + day
  TString base;
  if(!has_end){
    // Desde start hasta el final (cubre múltiples días)
    base.Form("(ymd > %d) || (ymd == %d && tsec >= %d)", ymd_s, ymd_s, ts_s);
  } else if(ymd_s == ymd_e){
    // Mismo día: entre tsec
    base.Form("(ymd == %d && tsec >= %d && tsec <= %d)", ymd_s, ts_s, ts_e);
  } else {
    // Días diferentes: (día intermedio) OR (borde inferior) OR (borde superior)
    base.Form("(ymd > %d && ymd < %d) || (ymd == %d && tsec >= %d) || (ymd == %d && tsec <= %d)",
              ymd_s, ymd_e, ymd_s, ts_s, ymd_e, ts_e);
  }

  if(file_id >= 0){
    base = TString::Format("(file_id == %d) && ( %s )", file_id, base.Data());
  }
  return TCut(base.Data());
}

/** 3: draw_range
    Abre un .root, toma el TTree "temps", define alias 'ymd',
    aplica el corte y dibuja la expresión (por defecto S1 vs hora fraccionaria).
    Opcional: guarda un subconjunto en out_subset (si no es vacío).
    - TFile::Open(): abre el archivo ROOT.
    - TTree::SetAlias(): define alias de columnas.
    - TTree::Draw(expr, sel, opt): grafica con selección y opciones.
    - TTree::CopyTree(sel): crea un TTree con solo las filas que cumplen sel.
    - TFile(outfile,"RECREATE"): escribe el subset en un nuevo archivo.
*/
void draw_range(const char* rootfile,
                const char* start,           // "YYYY-MM-DD HH:MM:SS"
                const char* end = "",        // "" => hasta el final
                const char* expr = "S1:(hour + minute/60.0 + second/3600.0)",
                int file_id = -1,            // -1 => todos; 0..N => solo ese file_id
                const char* out_subset = "") // "" => no guardar subset
{
  if(!rootfile || !*rootfile){ std::cerr << "[ERROR] rootfile vacío.\n"; return; }

  // Abrir archivo y árbol
  TFile* f = TFile::Open(rootfile, "READ");
  if(!f || f->IsZombie()){ std::cerr << "[ERROR] No pude abrir: " << rootfile << "\n"; return; }
  TTree* T = (TTree*)f->Get("temps");
  if(!T){ std::cerr << "[ERROR] No existe TTree 'temps' en el archivo.\n"; f->Close(); return; }

  // Alias para fecha compacta
  T->SetAlias("ymd","year*10000 + month*100 + day");

  // Corte
  TCut sel = build_sel(start, end, file_id);
  std::cout << "[INFO] Corte = " << sel.GetTitle() << "\n";
  std::cout << "[INFO] Entradas en el tramo = " << T->GetEntries(sel) << "\n";

  // Dibujo
  T->Draw(expr, sel, "l");

  // Guardar subset si se pidió
  if(out_subset && *out_subset){
    TTree* Tsub = T->CopyTree(sel);
    if(Tsub){
      TFile fout(out_subset, "RECREATE");
      Tsub->Write();
      fout.Close();
      std::cout << "[INFO] Subconjunto guardado en: " << out_subset << "\n";
    }
  }

  // Nota: dejamos el archivo abierto para que puedas seguir trabajando en ROOT.
}

/** 4: Ejemplos de uso
// Desde 2025-08-19 15:22:22 hasta el final del archivo
.x draw_range.C("temps_20250819.root","2025-08-19 15:22:22") Con este lo he ejecutado

// Entre dos tiempos específicos
.x draw_range.C("temps_20250819.root","2025-08-19 15:22:22","2025-08-20 07:59:22")

// Filtrar por file_id==0 (si juntaste varios logs) y eje X en horas fraccionarias
.x draw_range.C("temps_20250819.root",
                "2025-08-19 15:22:22",
                "2025-08-20 07:59:22",
                "S1:(hour + minute/60.0 + second/3600.0)",
                0)

// Guardar el subset en otro .root
.x draw_range.C("temps_20250819.root",
                "2025-08-19 15:22:22",
                "2025-08-20 07:59:22",
                "S1:(hour + minute/60.0 + second/3600.0)",
                -1,
                "subset_20250819_152222__to__20250820_075922.root")

*/
