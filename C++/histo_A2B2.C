// histo_A2B2.C
void histo_A2B2(){
  TFile* file = TFile::Open("data.root", "READ");
  TNtuple* ntuple = (TNtuple*)file->Get("matedata");
  float evn, A2, B2;
  
  ntuple->SetBranchAddress("evn", &evn);
  ntuple->SetBranchAddress("A2", &A2);
  ntuple->SetBranchAddress("B2", &B2);

  TH2D *density_1= new TH2D("density_2","signal density for A2 B2",12,0,12,12,0,12);
  TFile *new_file = new TFile("histo_A2_B2.root", "RECREATE");
  
   for (int i = 1; i < 3692190 ; ++i) {
        ntuple->GetEntry(i);
        
        density_1->Fill(A2,B2);

    }
  density_1->Draw("COLZ");
  density_1->Write();

}