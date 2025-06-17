//histo_A1B1.C
void histo_A1B1(){
  TFile* file = TFile::Open("data.root", "READ");
  TNtuple* ntuple = (TNtuple*)file->Get("matedata");
  float evn, A1, B1;
  
  ntuple->SetBranchAddress("evn", &evn);
  ntuple->SetBranchAddress("A1", &A1);
  ntuple->SetBranchAddress("B1", &B1);

  TH2D *density_1= new TH2D("density_1","signal density for A1 B1",12,0,12,12,0,12);
  TFile *new_file = new TFile("histo_A1_B1.root", "RECREATE");
  
   for (int i = 1; i < 3692190 ; ++i) {
        ntuple->GetEntry(i);
        
        density_1->Fill(A1,B1);

    }
  density_1->Draw("COLZ");
  density_1->Write();

}