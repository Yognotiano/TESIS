// make_tuple.C — Logs de temperatura -> ROOT TTree (multi-archivo) con salida en temp_root

#include <TFile.h>       // TFile: archivo ROOT (métodos: ctor, IsZombie(), Write(), Close())
#include <TTree.h>       // TTree: árbol (métodos: Branch(), Fill(), Write(), Print(), Draw())
#include <TList.h>       // TList: contenedor ROOT (métodos: SetOwner(), Add(), Write())
#include <TNamed.h>      // TNamed: objeto (name,title) almacenable
#include <TParameter.h>  // TParameter<T>: almacenable
#include <TString.h>     // TString + Form()
#include <TSystem.h>     // gSystem: utilidades de sistema (BaseName, OpenDirectory, FreeDirectory, mkdir, ExpandPathName)

#include <iostream>
#include <fstream>
#include <regex>
#include <string>
#include <vector>
#include <limits>
#include <cctype>
#include <cstdio>
#include <cstdlib>
#include <glob.h>
#include <cstring>   // strlen

/* 0: DESCRIPCIÓN GENERAL
   Lee líneas tipo:
     "YYYY-MM-DD,HH:MM:SS, Unidad: C°, S1: v1, ..., S19: v19."
   desde uno o varios archivos (literal, comodines, o lista separada por comas).
   Crea un TTree "temps" con ramas:
     year, month, day, hour, minute, second, tsec, file_id, S1..S19.
   Guardará SIEMPRE el .root dentro de:
     /Users/claudio/Documents/1_todo/Lab/Termometros/Root/temp_root
   Si la carpeta no existe, la crea automáticamente.
   El nombre del archivo de salida se auto-nombra por fechas extraídas
   de los nombres de archivo: temps_YYYYMMDD[ _YYYYMMDD ].root
*/

/** 1: Constantes de ruta de salida */
static const char* kBaseDir = "/Users/claudio/Documents/1_todo/Lab/Termometros/Root";
static const char* kSubDir  = "temp_root";

/** 2: trim_copy
    Quita espacios al inicio/fin de un string.
*/
static inline std::string trim_copy(std::string s){
  size_t a=0; while(a<s.size() && std::isspace((unsigned char)s[a])) ++a;
  size_t b=s.size(); while(b>a && std::isspace((unsigned char)s[b-1])) --b;
  return s.substr(a,b-a);
}

/** 3: has_glob
    Retorna true si el token tiene comodines (*, ?, [ ).
*/
static inline bool has_glob(const std::string& s){
  return s.find('*')!=std::string::npos || s.find('?')!=std::string::npos || s.find('[')!=std::string::npos;
}

/** 4: split_commas
    Separa por comas en tokens (ignorando espacios alrededor).
*/
static std::vector<std::string> split_commas(const std::string& s){
  std::vector<std::string> out; size_t i=0;
  while(i<s.size()){
    size_t j = s.find(',', i);
    std::string tok = (j==std::string::npos) ? s.substr(i) : s.substr(i, j-i);
    tok = trim_copy(tok);
    if(!tok.empty()) out.push_back(tok);
    if(j==std::string::npos) break;
    i = j+1;
  }
  return out;
}

/** 5: expand_one_token
    Expande un token con glob(3) si tiene comodines; si no, lo devuelve literal.
    - glob(): expande patrones del sistema.
    - globfree(): libera memoria reservada por glob().
*/
static std::vector<std::string> expand_one_token(const std::string& token){
  std::vector<std::string> files;
  if(has_glob(token)){
    glob_t g;
    int rc = glob(token.c_str(), 0, nullptr, &g);      /* método/función: glob — expansión de comodines */
    if(rc==0){
      for(size_t i=0;i<g.gl_pathc;++i) files.emplace_back(g.gl_pathv[i]);
    }
    globfree(&g);                                       /* método/función: globfree — libera recursos */
  }else{
    files.push_back(token);
  }
  return files;
}

/** 6: expand_inputs
    A partir de una cadena (lista con comas y/o comodines) retorna todos los archivos.
*/
static std::vector<std::string> expand_inputs(const std::string& inputs){
  std::vector<std::string> all;
  for(const auto& tok : split_commas(inputs)){
    auto v = expand_one_token(tok);
    all.insert(all.end(), v.begin(), v.end());
  }
  return all;
}

/** 7: join_path
    Une dos componentes de ruta con una sola '/' entre medio.
*/
static std::string join_path(const std::string& a, const std::string& b){
  if(a.empty()) return b;
  char last = a.back();
  if(last=='/' || last=='\\') return a + b;
  return a + "/" + b;
}

/** 8: basename_of
    Devuelve el nombre base (sin directorios) de una ruta.
    - gSystem->BaseName(): extrae la parte final del path (si gSystem está disponible).
*/
static std::string basename_of(const std::string& path){
  if(gSystem){
    const char* b = gSystem->BaseName(path.c_str());   /* método: BaseName — nombre base del path */
    return b ? std::string(b) : path;
  }
  size_t p = path.find_last_of("/\\");
  return (p==std::string::npos) ? path : path.substr(p+1);
}

/** 9: extract_date_yyyymmdd
    Extrae el prefijo "YYYYMMDD" del nombre base (p.ej., "20250819_0800-0800.TXT").
*/
static std::string extract_date_yyyymmdd(const std::string& filename_base){
  static const std::regex re(R"(^([0-9]{8}))");
  std::smatch m;
  if(std::regex_search(filename_base, m, re)) return m[1].str();
  return "";
}

/** 10: compute_span_from_filenames
     Devuelve {dmin, dmax} (YYYYMMDD) escaneando todos los nombres de archivo.
     YYYYMMDD ordena lexicográficamente igual que cronológicamente.
*/
static std::pair<std::string,std::string>
compute_span_from_filenames(const std::vector<std::string>& files){
  std::string dmin, dmax;
  for(const auto& f : files){
    std::string base = basename_of(f);
    std::string d = extract_date_yyyymmdd(base);
    if(d.empty()) continue;
    if(dmin.empty() || d < dmin) dmin = d;
    if(dmax.empty() || d > dmax) dmax = d;
  }
  return {dmin, dmax};
}

/** 11: pick_outfile_name
     Decide el NOMBRE (no la ruta) del archivo .root:
     - Si 'outfile_arg' es no vacío y != "auto", usa su base name.
     - Si está vacío o "auto", genera por fechas:
         temps_<dmin>.root           (si dmin==dmax y no vacío)
         temps_<dmin>_<dmax>.root    (si hay rango)
         temps.root                  (fallback)
*/
static std::string pick_outfile_name(const std::vector<std::string>& files,
                                     const char* outfile_arg){
  if(outfile_arg && std::strlen(outfile_arg)>0 && std::string(outfile_arg)!="auto"){
    // Forzamos a quedarnos con el base name para guardarlo SIEMPRE en temp_root
    return basename_of(outfile_arg);
  }
  auto [dmin, dmax] = compute_span_from_filenames(files);
  if(dmin.empty()) return "temps.root";
  if(dmin==dmax)   return "temps_" + dmin + ".root";
  return "temps_" + dmin + "_" + dmax + ".root";
}

/** 12: MetaHeader
     Estructura para la cabecera opcional "#Inicio: ...; Duracion: N"
*/
struct MetaHeader {
  std::string inicio;
  int duracion_min = -1;
  bool present = false;
};

/** 13: read_header_if_any
     Lee la primera línea del stream y parsea la cabecera si empieza con '#'.
     Si no hay cabecera, restaura el cursor al inicio.
     - std::getline(): lee una línea.
     - in.tellg()/in.seekg(): guarda/restaura posición del stream.
     - std::regex_search(): extrae campos con regex.
*/
static MetaHeader read_header_if_any(std::istream& in){
  MetaHeader mh;
  std::streampos pos0 = in.tellg();                 /* método: tellg — posición actual del stream */
  std::string line;
  if(std::getline(in,line)){                        /* método: getline — lee línea completa */
    if(!line.empty() && line[0]=='#'){
      std::regex reh(R"(#\s*Inicio:\s*([0-9\-]+\s+[0-9:]+)\s*;\s*Duracion:\s*([0-9]+))");
      std::smatch m;
      if(std::regex_search(line,m,reh)){            /* método: regex_search — busca patrón y captura */
        mh.inicio = m[1].str();
        mh.duracion_min = std::stoi(m[2].str());
        mh.present = true;
      }
    }else{
      in.clear();                                    /* método: clear — limpia flags de error */
      in.seekg(pos0);                                 /* método: seekg — mueve cursor a pos0 */
    }
  }
  return mh;
}

/** 14: ensure_output_dir
     Garantiza la creación/uso de la carpeta de salida "temp_root" bajo kBaseDir.
     Devuelve la ruta ABSOLUTA donde guardar (…/Root/temp_root).
     - gSystem->ExpandPathName(): expande rutas (tilde, etc.).
     - gSystem->OpenDirectory(): intenta abrir un directorio (existe?).
     - gSystem->FreeDirectory(): libera handle de OpenDirectory().
     - gSystem->mkdir(path, kTRUE): crea el directorio; kTRUE = recursivo.
*/
static std::string ensure_output_dir(){
  // Construye ruta base -> subdir
  std::string base = kBaseDir;
  std::string outdir = join_path(base, kSubDir);

  // Expandir (por si acaso; aquí es ruta absoluta fija)
  TString exp = outdir.c_str();
  gSystem->ExpandPathName(exp);                      /* método: ExpandPathName — expande variables/tilde */

  // ¿Existe?
  void* dirp = gSystem->OpenDirectory(exp.Data());  /* método: OpenDirectory — handle si existe, nullptr si no */
  if(dirp){
    gSystem->FreeDirectory(dirp);                    /* método: FreeDirectory — libera el handle */
    return exp.Data();                               // ya existe
  }

  // Si no existe, crearlo (recursivo)
  int rc = gSystem->mkdir(exp.Data(), kTRUE);       /* método: mkdir(path, recursive) — crea (0=ok) */
  if(rc!=0){
    std::cerr << "[ERROR] No se pudo crear la carpeta de salida: " << exp.Data() << "\n";
    return ""; // señal de error
  }
  return exp.Data();
}

/** 15: make_tuple (macro principal)
     Expande entradas, asegura el directorio de salida, auto-nombra el .root,
     crea el TTree y rellena con todos los archivos.
     Escribe además TList "files" (file_id->nombre) y "meta" (cabeceras).
     MÉTODOS ROOT CLAVE USADOS:
       - TFile(out, "RECREATE"): crea/sobrescribe archivo ROOT.
       - f.IsZombie(): detecta fallo al abrir/crear.
       - TTree ctor + Branch(): define columnas.
       - TTree::Fill(): añade una fila.
       - TTree::Write(): escribe el árbol.
       - TList::SetOwner(true), Add(), Write("name", kSingleKey): metadatos.
       - TFile::Close(): cierra y vuelca a disco.
*/
void make_tuple(const char* inputs="20250819_0800-0800.TXT",
                const char* outfile="") // vacío o "auto" => auto-nombre
{
  const int NSENS = 19;

  // 15.1 Expandir archivos de entrada
  std::vector<std::string> files = expand_inputs(inputs ? inputs : "");
  if(files.empty()){
    std::cerr << "No se encontraron archivos para: " << (inputs?inputs:"(vacío)") << "\n";
    return;
  }

  // 15.2 Asegurar carpeta de salida
  std::string outdir = ensure_output_dir();
  if(outdir.empty()) return; // no se pudo crear

  // 15.3 Elegir NOMBRE del archivo (sin ruta) y construir ruta completa en temp_root
  std::string outname = pick_outfile_name(files, outfile);
  std::string outpath = join_path(outdir, outname);
  std::cout << "[INFO] Archivo de salida: " << outpath << "\n";

  // 15.4 Crear archivo ROOT
  TFile f(outpath.c_str(), "RECREATE");             /* método: TFile ctor — crea/sobrescribe archivo ROOT */
  if(f.IsZombie()){                                  /* método: IsZombie — error al abrir/crear */
    std::cerr<<"No se pudo crear "<<outpath<<"\n"; 
    return; 
  }

  // 15.5 Definir árbol y ramas
  TTree T("temps","Temperaturas C (S1..S19) de múltiples archivos"); /* método: TTree ctor */

  unsigned int year,month,day,hour,minute,second;
  unsigned int tsec; // segundos desde medianoche
  int file_id;
  float S[NSENS+1];  // 1..NSENS

  T.Branch("year",&year,"year/i");                   /* método: Branch — crea rama tipo UInt_t */
  T.Branch("month",&month,"month/i");
  T.Branch("day",&day,"day/i");
  T.Branch("hour",&hour,"hour/i");
  T.Branch("minute",&minute,"minute/i");
  T.Branch("second",&second,"second/i");
  T.Branch("tsec",&tsec,"tsec/i");
  T.Branch("file_id",&file_id,"file_id/I");         /* I = Int_t */
  for(int i=1;i<=NSENS;++i){
    TString b=Form("S%d",i);
    T.Branch(b, &S[i], b+"/F");                     /* F = Float_t */
  }

  // 15.6 Metadatos auxiliares
  TList files_list; files_list.SetOwner(kTRUE);      /* método: SetOwner(true) — la lista destruye sus hijos */
  TList meta_list;  meta_list.SetOwner(kTRUE);

  std::regex reS(R"(S(\d+):\s*([-+]?\d+(?:\.\d+)?))");

  // 15.7 Procesar archivos
  for(size_t i=0;i<files.size(); ++i){
    file_id = static_cast<int>(i);
    const std::string& fname = files[i];
    files_list.Add(new TNamed(Form("file_%d",file_id), fname.c_str()));  /* método: Add — inserta objeto en lista */

    std::ifstream in(fname);                                             /* ctor ifstream — abre archivo texto */
    if(!in){ 
      std::cerr<<"[ADVERTENCIA] No puedo abrir "<<fname<<"\n"; 
      continue; 
    }

    MetaHeader mh = read_header_if_any(in);
    if(mh.present){
      meta_list.Add(new TNamed(Form("Inicio_%d",file_id), mh.inicio.c_str()));
      meta_list.Add(new TParameter<int>(Form("Duracion_min_%d",file_id), mh.duracion_min));
    }

    std::string line;
    while(std::getline(in,line)){                                        /* método: getline — lee línea */
      line = trim_copy(line);
      if(line.empty() || line[0]=='#') continue;
      if(!line.empty() && (line.back()=='.' || line.back()==',')) line.pop_back();

      for(int k=1;k<=NSENS;++k) S[k]=std::numeric_limits<float>::quiet_NaN();

      auto p1 = line.find(',');              if(p1==std::string::npos) continue;
      auto p2 = line.find(',', p1+1);        if(p2==std::string::npos) continue;

      std::string date = trim_copy(line.substr(0,p1));                  // "YYYY-MM-DD"
      std::string time = trim_copy(line.substr(p1+1, p2-(p1+1)));       // "HH:MM:SS"
      if(std::sscanf(date.c_str(), "%u-%u-%u", &year,&month,&day) != 3) continue; /* sscanf — parseo rápido */
      if(std::sscanf(time.c_str(), "%u:%u:%u", &hour,&minute,&second) != 3) continue;

      tsec = hour*3600u + minute*60u + second;

      std::string rest = line.substr(p2+1);
      for(std::sregex_iterator it(rest.begin(),rest.end(),reS), end; it!=end; ++it){
        int idx = std::stoi((*it)[1].str());
        if(idx>=1 && idx<=NSENS) S[idx] = std::stof((*it)[2].str());
      }

      T.Fill();                                                         /* método: Fill — escribe una fila */
    }
  }

  // 15.8 Escribir y cerrar
  T.Write();                                                            /* método: Write — serializa en el TFile */
  files_list.Write("files", TObject::kSingleKey);                       /* método: Write(name,kSingleKey) — guarda lista */
  meta_list.Write("meta",  TObject::kSingleKey);
  f.Close();                                                            /* método: Close — cierra archivo ROOT */

  std::cout<<"OK: escrito "<<outpath<<" con 'temps', 'files' y 'meta'.\n";
}

/** 16: EJEMPLOS DE USO
.x make_tuple.C("20250819_0800-0800.TXT")
  → crea /Users/claudio/Documents/1_todo/Lab/Termometros/Root/temp_root/temps_20250819.root

.x make_tuple.C("20250819_0800-0800.TXT,20250820_0800-0800.TXT")
  → crea /Users/claudio/Documents/1_todo/Lab/Termometros/Root/temp_root/temps_20250819_20250820.root

.x make_tuple.C("202508*.TXT")   // comodines
  → crea temps_<min>_<max>.root en temp_root

.x make_tuple.C("20250819_0800-0800.TXT","mi_salida.root")
  → guarda SIEMPRE en temp_root, usando SOLO el nombre base "mi_salida.root".
*/
