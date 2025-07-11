import {NgClass} from "@angular/common";
import {Component, inject, Input, OnInit} from "@angular/core";
import {FormsModule, NgForm} from "@angular/forms";
import {nodeResolverModel} from "@app/models/resolvers/node-resolver-model";
import {TranslatorPipe} from "@app/shared/pipes/translate";
import {NodeResolver} from "@app/shared/resolvers/node.resolver";
import {UtilsService} from "@app/shared/services/utils.service";
import {TranslateModule} from "@ngx-translate/core";

@Component({
  selector: "src-tab6",
  templateUrl: "./tab6.component.html",
  standalone: true,
  imports: [FormsModule, NgClass, TranslatorPipe, TranslateModule]
})
export class Tab6Component implements OnInit {
  @Input() contentForm: NgForm;
  nodeData: nodeResolverModel;
  backupEnabled: boolean = false;
  backupTime: string = '';
  backupDestinationPath: string = '';
  protected utilsService = inject(UtilsService);
  private nodeResolver = inject(NodeResolver);
  
  ngOnInit(): void {
    this.nodeData = this.nodeResolver.dataModel;
    if (this.nodeData.backup_enabled) {
      this.loadBackupInterval();
    }
  }
  loadBackupInterval() {
    this.backupEnabled = this.nodeData.backup_enabled;
    this.backupTime = this.formatBackupTime(this.nodeData.backup_time);
    this.backupDestinationPath = this.nodeData.backup_path;
  }
  formatBackupTime(iso8601: string): string {
    const match = iso8601.match(/(?:T)?(\d{2}):(\d{2})/);
    return match ? `${match[1]}:${match[2]}` : '00:00';
  }
  save(): void {
    this.nodeData.backup_enabled = this.backupEnabled;
    this.nodeData.backup_time = this.backupTime;
    this.nodeData.backup_path = this.backupDestinationPath;
    this.utilsService.update(this.nodeResolver.dataModel).subscribe(_ => {})
  }
}