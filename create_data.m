% MATLAB脚本：数据计算和图表生成
% 此脚本在无人值守情况下运行，生成数据并保存结果

function create_data()
    try
        % 设置输出目录
        outputDir = 'output';
        if ~exist(outputDir, 'dir')
            mkdir(outputDir);
        end
        
        % 生成示例数据
        fprintf('开始生成数据...\n');
        
        % 创建时间序列数据
        t = 0:0.1:10;
        y1 = sin(t) + 0.1*randn(size(t));
        y2 = cos(t) + 0.1*randn(size(t));
        y3 = sin(2*t) + 0.1*randn(size(t));
        
        % 创建分类数据
        categories = {'A', 'B', 'C', 'D', 'E'};
        values = [23, 45, 56, 78, 32];
        
        % 创建散点图数据
        x_scatter = randn(100, 1);
        y_scatter = 2*x_scatter + randn(100, 1);
        
        % 计算统计信息
        stats = struct();
        stats.mean_y1 = mean(y1);
        stats.std_y1 = std(y1);
        stats.mean_y2 = mean(y2);
        stats.std_y2 = std(y2);
        stats.correlation = corr(x_scatter, y_scatter);
        
        % 保存数据到JSON文件
        data = struct();
        data.time_series = struct();
        data.time_series.t = t;
        data.time_series.y1 = y1;
        data.time_series.y2 = y2;
        data.time_series.y3 = y3;
        
        data.categorical = struct();
        data.categorical.categories = categories;
        data.categorical.values = values;
        
        data.scatter = struct();
        data.scatter.x = x_scatter;
        data.scatter.y = y_scatter;
        
        data.statistics = stats;
        data.timestamp = datestr(now, 'yyyy-mm-dd HH:MM:SS');
        
        % 保存JSON数据
        jsonFile = fullfile(outputDir, 'data.json');
        jsonStr = jsonencode(data);
        fid = fopen(jsonFile, 'w');
        if fid ~= -1
            fprintf(fid, '%s', jsonStr);
            fclose(fid);
            fprintf('数据已保存到: %s\n', jsonFile);
        else
            error('无法创建JSON文件');
        end
        
        % 生成图表并保存
        fprintf('开始生成图表...\n');
        
        % 图1: 时间序列图
        fig1 = figure('Visible', 'off');
        plot(t, y1, 'b-', 'LineWidth', 2, 'DisplayName', 'sin(t)');
        hold on;
        plot(t, y2, 'r-', 'LineWidth', 2, 'DisplayName', 'cos(t)');
        plot(t, y3, 'g-', 'LineWidth', 2, 'DisplayName', 'sin(2t)');
        xlabel('时间');
        ylabel('数值');
        title('时间序列图');
        legend('Location', 'best');
        grid on;
        
        % 保存时间序列图
        timeSeriesFile = fullfile(outputDir, 'time_series.png');
        saveas(fig1, timeSeriesFile);
        close(fig1);
        fprintf('时间序列图已保存到: %s\n', timeSeriesFile);
        
        % 图2: 柱状图
        fig2 = figure('Visible', 'off');
        bar(values);
        set(gca, 'XTickLabel', categories);
        xlabel('类别');
        ylabel('数值');
        title('分类数据柱状图');
        grid on;
        
        % 保存柱状图
        barFile = fullfile(outputDir, 'bar_chart.png');
        saveas(fig2, barFile);
        close(fig2);
        fprintf('柱状图已保存到: %s\n', barFile);
        
        % 图3: 散点图
        fig3 = figure('Visible', 'off');
        scatter(x_scatter, y_scatter, 50, 'filled', 'MarkerFaceAlpha', 0.6);
        xlabel('X');
        ylabel('Y');
        title(sprintf('散点图 (相关系数: %.3f)', stats.correlation));
        grid on;
        
        % 保存散点图
        scatterFile = fullfile(outputDir, 'scatter_plot.png');
        saveas(fig3, scatterFile);
        close(fig3);
        fprintf('散点图已保存到: %s\n', scatterFile);
        
        % 图4: 综合图表
        fig4 = figure('Visible', 'off');
        subplot(2,2,1);
        plot(t, y1, 'b-', 'LineWidth', 2);
        title('sin(t)');
        grid on;
        
        subplot(2,2,2);
        bar(values);
        set(gca, 'XTickLabel', categories);
        title('分类数据');
        
        subplot(2,2,3);
        scatter(x_scatter, y_scatter, 30, 'filled');
        title('散点图');
        grid on;
        
        subplot(2,2,4);
        histogram(y1, 20);
        title('y1分布');
        grid on;
        
        % 保存综合图表
        combinedFile = fullfile(outputDir, 'combined_chart.png');
        saveas(fig4, combinedFile);
        close(fig4);
        fprintf('综合图表已保存到: %s\n', combinedFile);
        
        % 创建状态文件
        statusFile = fullfile(outputDir, 'status.txt');
        fid = fopen(statusFile, 'w');
        if fid ~= -1
            fprintf(fid, 'MATLAB脚本执行成功\n');
            fprintf(fid, '执行时间: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'));
            fprintf(fid, '生成文件:\n');
            fprintf(fid, '- data.json\n');
            fprintf(fid, '- time_series.png\n');
            fprintf(fid, '- bar_chart.png\n');
            fprintf(fid, '- scatter_plot.png\n');
            fprintf(fid, '- combined_chart.png\n');
            fclose(fid);
        end
        
        fprintf('MATLAB脚本执行完成！\n');
        fprintf('所有文件已保存到: %s\n', outputDir);
        
    catch ME
        % 错误处理
        fprintf('MATLAB脚本执行出错: %s\n', ME.message);
        
        % 创建错误状态文件
        errorDir = 'output';
        if ~exist(errorDir, 'dir')
            mkdir(errorDir);
        end
        
        errorFile = fullfile(errorDir, 'error.txt');
        fid = fopen(errorFile, 'w');
        if fid ~= -1
            fprintf(fid, 'MATLAB脚本执行失败\n');
            fprintf(fid, '错误时间: %s\n', datestr(now, 'yyyy-mm-dd HH:MM:SS'));
            fprintf(fid, '错误信息: %s\n', ME.message);
            fclose(fid);
        end
        
        rethrow(ME);
    end
end

% 执行主函数
create_data();
