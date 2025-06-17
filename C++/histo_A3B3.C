//histo_A3B3.C
void histo_A3B3(){
  TFile* file = TFile::Open("data.root", "READ");
  TNtuple* ntuple = (TNtuple*)file->Get("matedata");
  float evn, A3, B3;
  
  ntuple->SetBranchAddress("evn", &evn);
  ntuple->SetBranchAddress("A3", &A3);
  ntuple->SetBranchAddress("B3", &B3);

  TH2D *density_1= new TH2D("density_3","signal density for A3 B3",12,0,12,12,0,12);
  TFile *new_file = new TFile("histo_A3_B3.root", "RECREATE");
  
   for (int i = 1; i < 3692190 ; ++i) {
        ntuple->GetEntry(i);
        
        density_1->Fill(A3,B3);

    }
  density_1->Draw("COLZ");
  density_1->Write();

}